# -----------------------------------------------------------------------------
# Hermes OSINT - V2.0 Alpha
# This project is currently in an alpha state.
# -----------------------------------------------------------------------------

import os
import io
import tarfile
import tempfile
import shutil
import time
import json
from typing import List, Dict, Optional
import docker
from docker.errors import APIError, ImageNotFound, DockerException, NotFound
import logging
from .security_error import SecurityError

logger = logging.getLogger(__name__)
# Assumed to exist in your code base:
# TRUSTED_IMAGES: Dict[str, str]  # mapping logical name -> "repo@sha256:..."
# ALLOWED_ENV_VARS: Set[str]
# logger: logging.Logger
# SecurityError: custom exception class

class DockerManager:
    """
    DockerManager with stronger ephemeral/OPSEC behavior:
    - extracts files reliably via get_archive
    - uses tmpfs and non-root user
    - supports seccomp/apparmor hooks
    - creates ephemeral networks when requested
    - fully removes container/image and attempts to erase traces
    """

    TRUSTED_IMAGES = {
    "sherlock/sherlock": "sherlock/sherlock@sha256:9d6602b98179fb15ceab88433626fb0ae603ae9880e13cab886970317fe1475f",
    "khast3x/h8mail": "khast3x/h8mail@sha256:baa9be41369e6d2e966d640c0d0b9d0856cf62d1c0cfbfc91d8d035760b160a9",
    "searxng/searxng":"searxng/searxng@sha256:0124d32d77e0c7360d0b85f5d91882d1837e6ceb243c82e190f5d7e9f1401334",
    "projectdiscovery/subfinder":"projectdiscovery/subfinder@sha256:70d8fa85be31de07d4aee7f7058effb83f9e5322154417c4267fddb6a4d79d99",
    "ghcr.io/laramies/theharvester:sha-af61197":"ghcr.io/laramies/theharvester:sha-af61197@sha256:5836bcb85ed30ac55391a329b1eb6b12aa6430d31118ab1d3afdd47786a42731",
    "sundowndev/phoneinfoga":"sundowndev/phoneinfoga@sha256:0706f55ef1eeae1352ea4f48f57a3490c8ea87ac055aa6d4491f72405c36e445",
    # NOTE: s0md3v/photon is typically built locally, not pulled from a registry
    # This is a placeholder SHA256 - update with actual digest if using a published image
    "s0md3v/photon":"s0md3v/photon@sha256:0000000000000000000000000000000000000000000000000000000000000000",
    # Untrusted Images are below - Replace images with trusted images/custom images
    "ai2ys/exiftool":"ai2ys/exiftool@sha256:8a4e5be8cba9b234518c1b53c6645e8857508e684849564ab81b5bac1f6b5a48",
    "gmrnonoss/holehe":"gmrnonoss/holehe@sha256:c50267f3664cf26a4be242899d95e86b1cd82d0aad3085df5e74387d1de8bbc8"
    }

    # SECURITY: Whitelist for environment variables
    ALLOWED_ENV_VARS = {"HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "SOCKS_PROXY"}

    def __init__(self, reconnect_attempts: int = 3, reconnect_delay: float = 1.0):
        self.client = None
        self.reconnect_attempts = reconnect_attempts
        self.reconnect_delay = reconnect_delay
        self._connect()

    def _connect(self):
        """Establish connection to Docker daemon; retry briefly if flakey."""
        for attempt in range(1, self.reconnect_attempts + 1):
            try:
                self.client = docker.from_env()
                # quick ping to ensure it's usable
                self.client.ping()
                logger.info("Connected to Docker daemon")
                return
            except DockerException as exc:
                logger.warning(f"Failed to connect to docker (attempt {attempt}): {exc}")
                self.client = None
                time.sleep(self.reconnect_delay)
        # final state: client might be None
        if self.client is None:
            logger.error("Could not connect to Docker after retries")

    @property
    def is_available(self) -> bool:
        return self.client is not None

    def _ensure_client(self):
        if not self.is_available:
            self._connect()
            if not self.is_available:
                raise RuntimeError("Docker is not available")

    # --------------------
    # Helper: ephemeral temp dir
    # --------------------
    def _create_tempdir(self, prefix: str = "hermes_") -> str:
        d = tempfile.mkdtemp(prefix=prefix)
        # tighten perms
        os.chmod(d, 0o700)
        return d

    def _secure_delete_dir(self, path: str, passes: int = 1):
        """
        Best-effort secure deletion of files in a directory:
        - Overwrite files with zero bytes (attempt), then unlink.
        - Finally remove directory tree.
        Note: true secure deletion depends on filesystem; this is best-effort.
        WARNING: On modern SSDs/Flash storage with wear leveling, this does NOT guarantee data destruction.
        For high security, use encrypted volumes or RAM disks.
        """
        try:
            if not os.path.exists(path):
                return
            for root, dirs, files in os.walk(path, topdown=False):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        size = os.path.getsize(fp)
                        with open(fp, "wb") as fh:
                            # write zero bytes once (multiple passes expensive on slow disks)
                            fh.write(b"\x00" * min(4096, size or 1))
                            # try to truncate to zero to clear metadata
                            fh.truncate(0)
                    except Exception as e:
                        logger.debug(f"Secure overwrite failed for {fp}: {e}")
                    try:
                        os.remove(fp)
                    except Exception as e:
                        logger.debug(f"Removing file failed {fp}: {e}")
                for d in dirs:
                    dp = os.path.join(root, d)
                    try:
                        os.rmdir(dp)
                    except Exception:
                        # will be removed by shutil.rmtree later
                        pass
            # final removal
            shutil.rmtree(path, ignore_errors=True)
        except Exception as e:
            logger.warning(f"Secure delete directory {path} failed: {e}")

    # --------------------
    # Helper: ephemeral network
    # --------------------
    def _create_ephemeral_network(self, prefix: str = "hermes-net-") -> str:
        """
        Create a docker bridge network with a random name. Return network id.
        Caller must remove it when done.
        """
        name = f"{prefix}{int(time.time()*1000)}"
        try:
            net = self.client.networks.create(name, driver="bridge", internal=False)
            logger.debug(f"Created ephemeral network {name}")
            return net.name
        except APIError as e:
            logger.warning(f"Failed to create network {name}: {e}")
            return ""  # signal none created

    def _remove_network(self, name: str):
        if not name:
            return
        try:
            net = self.client.networks.get(name)
            net.remove()
            logger.debug(f"Removed network {name}")
        except NotFound:
            pass
        except Exception as e:
            logger.warning(f"Failed to remove network {name}: {e}")

    # --------------------
    # Image pull + digest verify (keeps your repo-digest check)
    # --------------------
    def pull_image(self, image_name: str):
        self._ensure_client()
        if image_name not in self.TRUSTED_IMAGES:
            raise ValueError("Untrusted image")

        trusted_ref = self.TRUSTED_IMAGES[image_name]  # repo@sha256:...
        try:
            logger.info(f"Pulling {trusted_ref}")
            image = self.client.images.pull(trusted_ref)
            repo_digests = image.attrs.get("RepoDigests", []) or []
            if trusted_ref not in repo_digests:
                # remove bad image
                try:
                    self.client.images.remove(image.id, force=True)
                except Exception:
                    pass
                raise SecurityError("Digest verification failed")
            logger.info(f"Image {trusted_ref} verified")
            return image
        except ImageNotFound:
            logger.error(f"Image not found: {trusted_ref}")
            raise
        except APIError as e:
            logger.error(f"Failed pulling image {trusted_ref}: {e}")
            raise

    def remove_image(self, image_name: str, force: bool = False):
        self._ensure_client()
        if image_name not in self.TRUSTED_IMAGES:
            raise ValueError("Cannot remove untrusted image")
        trusted_image = self.TRUSTED_IMAGES[image_name]
        try:
            self.client.images.remove(trusted_image, force=force)
            logger.info(f"Removed image {trusted_image}")
            return True
        except ImageNotFound:
            return False
        except APIError as e:
            logger.warning(f"Failed to remove image {trusted_image}: {e}")
            raise

    # --------------------
    # Extraction: get files from container path to host dir
    # --------------------
    def _extract_path_from_container(self, container, container_path: str, host_dest: str):
        """
        Uses container.get_archive to pull a path (file or directory) into host_dest.
        """
        try:
            stream, stat = container.get_archive(container_path)
        except Exception as e:
            logger.debug(f"get_archive failed for {container_path}: {e}")
            return False

        # stream is a raw tar stream; extract into host_dest
        try:
            file_like = io.BytesIO()
            for chunk in stream:
                file_like.write(chunk)
            file_like.seek(0)
            with tarfile.open(fileobj=file_like) as tf:
                # SECURITY: Prevent Zip Slip vulnerability
                for member in tf.getmembers():
                    self._safe_extract(tf, member, host_dest)
            return True
        except Exception as e:
            logger.error(f"Failed to extract archive for {container_path}: {e}")
            return False

    def _safe_extract(self, tar, member, path):
        """
        Safely extract a tar member, preventing Zip Slip.
        """
        # Resolve the destination path
        dest_path = os.path.abspath(path)
        # Resolve the member path
        member_path = os.path.abspath(os.path.join(dest_path, member.name))
        
        # Check if the member path is within the destination path
        if not member_path.startswith(dest_path):
            raise SecurityError(f"Attempted Zip Slip attack: {member.name}")
            
        # Extract the member
        tar.extract(member, path)

    # --------------------
    # Cleanup: check for leftover docker container metadata dirs
    # --------------------
    def _cleanup_leftover_container_dirs(self, container_id: str):
        """
        Best-effort: remove leftover container metadata under /var/lib/docker/containers/<id>
        NOTE: requires host permissions to succeed.
        """
        docker_cont_root = "/var/lib/docker/containers"
        try:
            candidate = os.path.join(docker_cont_root, container_id)
            if os.path.exists(candidate):
                logger.debug(f"Found leftover container dir {candidate}, attempting removal")
                # Best-effort: try to remove logs & dir
                try:
                    # remove log files first
                    for root, dirs, files in os.walk(candidate):
                        for f in files:
                            fp = os.path.join(root, f)
                            try:
                                os.remove(fp)
                            except Exception:
                                pass
                    shutil.rmtree(candidate, ignore_errors=True)
                    logger.debug(f"Removed leftover container dir {candidate}")
                except Exception as e:
                    logger.debug(f"Failed removing leftover dir {candidate}: {e}")
        except Exception as e:
            logger.debug(f"Leftover cleanup error: {e}")

    # --------------------
    # Main: run_container (ephemeral, extracts files, eradicates traces)
    # --------------------
    def run_container(
        self,
        image_name: str,
        command: List[str],
        environment: Optional[Dict] = None,
        timeout: int = 300,
        cleanup_image: bool = False,
        allow_network: bool = False,
        copy_paths: Optional[List[str]] = None,  # list of container paths to extract (e.g. ["/results", "/output.json"])
        seccomp_profile_path: Optional[str] = None,
        apparmor_profile: Optional[str] = None,
        user: str = "65534:65534",  # nobody:nogroup
    ) -> Dict:
        """
        Returns a dict with:
          - logs: str (truncated)
          - extracted_dir: path on host where copied files live (temporary)
          - exit_code: int
          - metadata: dict
        Steps:
          1. Ensure image exists (pull if needed)
          2. Create host tempdir and bind mount it to /hermes_results
          3. Optionally create ephemeral network
          4. Run container with strict options
          5. Wait (with timeout), gather logs
          6. Extract requested paths (copy to host tempdir)
          7. Remove container
          8. Remove image if requested
          9. Cleanup network
         10. Attempt to remove leftover docker metadata
        """
        self._ensure_client()
        if image_name not in self.TRUSTED_IMAGES:
            raise ValueError("Untrusted image")

        trusted_image = self.TRUSTED_IMAGES[image_name]

        # filter environment
        filtered_env = None
        if environment:
            filtered_env = {k: v for k, v in environment.items() if k in self.ALLOWED_ENV_VARS}
            if len(filtered_env) != len(environment):
                logger.warning("Filtered some environment variables")

        # ensure image present
        try:
            self.client.images.get(trusted_image)
        except ImageNotFound:
            self.pull_image(image_name)

        # prepare ephemeral host dir for results
        host_tempdir = self._create_tempdir()
        container_mount_path = "/hermes_results"

        # ephemeral network
        network_name = ""
        if allow_network:
            network_name = self._create_ephemeral_network()

        container = None
        container_id = None
        start_time = time.time()
        try:
            run_kwargs = dict(
                image=trusted_image,
                command=command,
                environment=filtered_env,
                detach=True,
                user=user,
                remove=False,  # we will remove after extraction
                mem_limit="768m",
                memswap_limit="768m",
                cpu_quota=50000,
                pids_limit=64,
                network_mode=None if allow_network else "none",  # default: no network unless allowed
                volumes={host_tempdir: {"bind": container_mount_path, "mode": "rw"}},
                tmpfs={"/tmp": "size=64m,noexec,nosuid"},
                privileged=False,
                cap_drop=["ALL"],
                security_opt=["no-new-privileges"],
                log_config={"type": "json-file", "config": {"max-size": "1m", "max-file": "1"}},  # Limited logging for output retrieval
            )

            # add seccomp and apparmor if provided (host paths)
            secopts = []
            if seccomp_profile_path and os.path.exists(seccomp_profile_path):
                secopts.append(f"seccomp={seccomp_profile_path}")
            if apparmor_profile:
                secopts.append(f"apparmor={apparmor_profile}")
            if secopts:
                run_kwargs["security_opt"] = run_kwargs.get("security_opt", []) + secopts

            # If a network is created use it
            if allow_network and network_name:
                # attach container to that network after creating it
                # run container with network disabled first, then connect
                run_kwargs["network_mode"] = "none"

            logger.info(f"Starting container from {trusted_image} cmd={command}")
            container = self.client.containers.run(**run_kwargs)
            container_id = container.id[:12]
            logger.debug(f"Started container {container_id}")

            # if we created a dedicated network, connect container to it now
            if allow_network and network_name:
                try:
                    net = self.client.networks.get(network_name)
                    net.connect(container)
                except Exception as e:
                    logger.warning(f"Failed to connect container to net {network_name}: {e}")

            # wait with timeout
            try:
                result = container.wait(timeout=timeout)
                exit_code = result.get("StatusCode", 0)
            except Exception as e:
                logger.error(f"Container timed out or wait error: {e}")
                try:
                    container.kill()
                except Exception:
                    pass
                raise RuntimeError(f"Container execution timeout after {timeout}s")

            # gather logs (truncate)
            MAX_LOG_SIZE = 5 * 1024 * 1024  # 5MB
            logs = ""
            try:
                raw = container.logs(tail=10000)
                logs = raw.decode("utf-8", errors="replace")
                if len(logs) > MAX_LOG_SIZE:
                    logs = logs[-MAX_LOG_SIZE:]
                    logs = "[LOG TRUNCATED]\n" + logs
            except Exception as e:
                logger.debug(f"Could not read logs: {e}")
                logs = f"[ERROR READING LOGS: {e}]"

            # extract requested paths (if none provided, attempt to copy /hermes_results)
            extracted_success = {}
            extraction_root = host_tempdir  # files will be available here

            if not copy_paths:
                copy_paths = [container_mount_path]

            for p in copy_paths:
                ok = self._extract_path_from_container(container, p, extraction_root)
                extracted_success[p] = ok

            metadata = {
                "container_id": container.id if container else None,
                "exit_code": exit_code,
                "runtime_seconds": time.time() - start_time,
                "extracted": extracted_success,
            }

            return {"logs": logs, "extracted_dir": extraction_root, "exit_code": exit_code, "metadata": metadata}

        except Exception as e:
            logger.error(f"Error running ephemeral container: {e}")
            # if we created a host_tempdir, attempt secure deletion
            try:
                if os.path.exists(host_tempdir):
                    self._secure_delete_dir(host_tempdir)
            except Exception:
                pass
            raise
        finally:
            # Always attempt to remove container
            if container:
                try:
                    container.remove(force=True)
                    logger.debug(f"Removed container {container_id}")
                except Exception as e:
                    logger.warning(f"Failed to remove container {container_id}: {e}")

            # Remove image if OPSEC requested
            if cleanup_image:
                try:
                    self.remove_image(image_name, force=True)
                except Exception as e:
                    logger.warning(f"Cleanup image failed: {e}")

            # Remove ephemeral network
            if network_name:
                self._remove_network(network_name)

            # Explicitly prune system to remove any dangling logs
            # When a container is removed, logs are deleted, but we prune to be certain
            try:
                self.client.containers.prune()
                logger.debug("Pruned container system to remove logs")
            except Exception as e:
                logger.debug(f"Failed to prune containers: {e}")

            # attempt to remove leftover docker container metadata directories (best-effort)
            if container_id:
                try:
                    self._cleanup_leftover_container_dirs(container.id)
                except Exception:
                    pass

    # --------------------
    # Convenience: fully ephemeral run helper that extracts results and then securely deletes them
    # --------------------
    def run_and_return_and_destroy(self, *args, secure_delete_results: bool = False, **kwargs) -> Dict:
        """
        Wrapper: run_container(...), then optionally secure-delete the extracted files.
        Returns what run_container returned (but if secure_delete_results=True, extracted_dir will be gone).
        """
        res = self.run_container(*args, **kwargs)
        extracted_dir = res.get("extracted_dir")
        if secure_delete_results and extracted_dir:
            try:
                self._secure_delete_dir(extracted_dir)
                logger.info("Secure-deleted extracted results")
                res["extracted_dir"] = None
            except Exception as e:
                logger.warning(f"Failed secure-delete extracted dir: {e}")
        return res
