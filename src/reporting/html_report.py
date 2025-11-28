import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger("OSINT_Tool")


def generate_html_report(results: Dict[str, Any], output_file: str):
    """
    Generate a beautiful HTML report with tiered results (Confirmed vs Possible).
    
    Args:
        results: Results dictionary
        output_file: Output file path
    """
    logger.info(f"Generating HTML report: {output_file}")
    
    target = results.get('target', 'Unknown')
    target_type = results.get('target_type', 'Unknown')
    stats = results.get('statistics', {})
    
    # Calculate totals
    total_results = stats.get('total_unique', 0)
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'unsafe-inline'; img-src 'self' data: https:;">
    <meta http-equiv="X-Content-Type-Options" content="nosniff">
    <meta http-equiv="X-Frame-Options" content="DENY">
    <meta http-equiv="Referrer-Policy" content="no-referrer">
    <title>OSINT Report - {target}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .header p {{ font-size: 1.1em; opacity: 0.9; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s;
        }}
        .stat-card:hover {{ transform: translateY(-5px); }}
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }}
        .stat-label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .section {{
            padding: 30px;
        }}
        .section h2 {{
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #eee;
        }}
        tr:hover {{ background: #f8f9fa; }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        .badge-confirmed {{ background: #28a745; color: white; }}
        .badge-possible {{ background: #ffc107; color: #333; }}
        .badge-high {{ background: #28a745; color: white; }}
        .badge-medium {{ background: #ffc107; color: #333; }}
        .badge-low {{ background: #dc3545; color: white; }}
        
        .email-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        .email-box {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
        }}
        .email-box h3 {{ margin-bottom: 15px; color: #555; }}
        .email-item {{
            background: white;
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 5px;
            border-left: 4px solid #ddd;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .email-confirmed {{ border-left-color: #28a745; }}
        .email-possible {{ border-left-color: #ffc107; }}
        
        .source-tag {{
            font-size: 0.8em;
            color: #666;
            background: #eee;
            padding: 2px 8px;
            border-radius: 10px;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 OSINT Report</h1>
            <p><strong>Target:</strong> {target} ({target_type})</p>
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Findings</div>
                <div class="stat-number">{total_results}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Confirmed</div>
                <div class="stat-number">{stats.get('confirmed_count', 0)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Possible</div>
                <div class="stat-number">{stats.get('possible_count', 0)}</div>
            </div>
        </div>
"""
    
    # Email Enumeration Section
    if 'emails' in results and results['emails']:
        emails_data = results['emails']
        confirmed = emails_data.get('confirmed_emails', [])
        possible = emails_data.get('possible_emails', [])
        
        html_content += f"""
        <div class="section">
            <h2>📧 Email Intelligence</h2>
            <div class="email-grid">
                <div class="email-box">
                    <h3>✅ Confirmed Emails ({len(confirmed)})</h3>
                    <p style="font-size: 0.9em; color: #666; margin-bottom: 10px;">Verified via Breach Data or PGP</p>
"""
        if confirmed:
            for item in confirmed:
                email = item.get('email', 'Unknown')
                source = item.get('source', 'Unknown')
                conf = item.get('confidence', 1.0)
                html_content += f"""
                    <div class="email-item email-confirmed">
                        <strong>{email}</strong>
                        <div>
                            <span class="source-tag">{source}</span>
                            <span class="badge badge-confirmed">{int(conf*100)}%</span>
                        </div>
                    </div>
"""
        else:
            html_content += "<p>No confirmed emails found.</p>"
            
        html_content += """
                </div>
                <div class="email-box">
                    <h3>⚠️ Possible Emails</h3>
                    <p style="font-size: 0.9em; color: #666; margin-bottom: 10px;">Generated from patterns & MX checked</p>
"""
        if possible:
            for item in possible[:20]: # Limit to top 20 to avoid clutter
                email = item.get('email', 'Unknown')
                source = item.get('source', 'Pattern')
                conf = item.get('confidence', 0.5)
                html_content += f"""
                    <div class="email-item email-possible">
                        <span>{email}</span>
                        <div>
                            <span class="source-tag">{source}</span>
                            <span class="badge badge-possible">{int(conf*100)}%</span>
                        </div>
                    </div>
"""
            if len(possible) > 20:
                html_content += f"<p>...and {len(possible)-20} more</p>"
        else:
            html_content += "<p>No possible emails found.</p>"
            
        html_content += """
                </div>
            </div>
        </div>
"""
    
    # Social Media Section
    social_media = results.get('social_media', [])
    if social_media:
        html_content += """
        <div class="section">
            <h2>👥 Social Media Profiles</h2>
            <table>
                <thead>
                    <tr>
                        <th>Platform</th>
                        <th>URL</th>
                        <th>Source</th>
                        <th>Confidence</th>
                    </tr>
                </thead>
                <tbody>
"""
        for profile in social_media:
            conf = profile.get('confidence', 0.0)
            badge_class = 'badge-high' if conf >= 0.8 else ('badge-medium' if conf >= 0.5 else 'badge-low')
            
            html_content += f"""                    <tr>
                        <td><strong>{profile.get('platform', 'N/A')}</strong></td>
                        <td><a href="{profile.get('url', '#')}" target="_blank">{profile.get('url', 'N/A')}</a></td>
                        <td><span class="source-tag">{profile.get('source', 'Unknown')}</span></td>
                        <td><span class="badge {badge_class}">{int(conf*100)}%</span></td>
                    </tr>
"""
        
        html_content += """                </tbody>
            </table>
        </div>
"""
    
    # Footer
    html_content += """
        <div class="footer">
            <p>Generated by Hermes OSINT Tool | v1.3</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"✓ HTML report saved to {output_file}")
