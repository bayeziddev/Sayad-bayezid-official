import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, Optional


def run_lighthouse_optimization(
    url: str, device: str = "mobile", output_dir: str = "./lighthouse_results"
) -> Optional[Dict[str, Any]]:
    """Runs an optimized, headless Google Lighthouse audit to capture render metrics."""
    # Ensure Lighthouse runner is accessible
    if not shutil.which("lighthouse"):
        print(
            "Error: Lighthouse CLI is missing! Please install it via: 'npm install -g lighthouse'"
        )
        return None

    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_name = f"portfolio_{device}_{timestamp}"

    json_path = os.path.join(output_dir, f"{report_name}.json")
    html_path = os.path.join(output_dir, f"{report_name}.html")

    # Isolated browser parameters to guarantee 0% local background noise skewing stats
    command = [
        "lighthouse",
        url,
        "--output=json",
        "--output=html",
        f"--output-path={os.path.join(output_dir, report_name)}",
        f"--form-factor={device}",
        "--chrome-flags=--headless --disable-gpu --no-sandbox --disable-software-rasterizer --disable-extensions",
        "--quiet",
    ]

    print(f"🚀 Launching isolated Chrome Engine to audit: {url} [{device.upper()}]...")

    try:
        # Run audit engine
        subprocess.run(command, check=True, capture_output=True, text=True)

        # Parse generated performance file
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        categories = data.get("categories", {})
        audits = data.get("audits", {})

        # Clean mapping wrapper 
        optimized_summary = {
            "target": url,
            "device": device,
            "html_report": html_path,
            "performance_score": int(categories.get("performance", {}).get("score", 0) * 100),
            "accessibility_score": int(categories.get("accessibility", {}).get("score", 0) * 100),
            "seo_score": int(categories.get("seo", {}).get("score", 0) * 100),
            "core_vitals": {
                "First Contentful Paint (FCP)": audits.get("first-contentful-paint", {}).get("displayValue", "N/A"),
                "Largest Contentful Paint (LCP)": audits.get("largest-contentful-paint", {}).get("displayValue", "N/A"),
                "Total Blocking Time (TBT)": audits.get("total-blocking-time", {}).get("displayValue", "N/A"),
                "Cumulative Layout Shift (CLS)": audits.get("cumulative-layout-shift", {}).get("displayValue", "N/A"),
                "Speed Index": audits.get("speed-index", {}).get("displayValue", "N/A"),
            },
            "critical_issues": []
        }

        # Automatically crawl for render-blocking and layout-shifting items
        optimization_checks = ["render-blocking-resources", "unused-javascript", "unused-css-rules", "modern-image-formats"]
        for check in optimization_checks:
            audit_item = audits.get(check, {})
            if audit_item.get("score", 1.0) < 0.85: # Flag items pulling down performance
                optimized_summary["critical_issues"].append({
                    "issue": audit_item.get("title"),
                    "impact": audit_item.get("displayValue", "Needs Optimization"),
                    "fix_guide": audit_item.get("description")
                })

        return optimized_summary

    except subprocess.CalledProcessError as e:
        print(f"❌ Lighthouse Engine Failed: {e.stderr}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"❌ Error compiling logs: {e}", file=sys.stderr)
        return None


if __name__ == "__main__":
    # Your live portfolio website URL
    LIVE_URL = "https://github.io"

    # Running Mobile configuration (Google's main rank index baseline)
    metrics = run_lighthouse_optimization(LIVE_URL, device="mobile")

    if metrics:
        print("\n" + "="*50)
        print(f"🏆 AUDIT RESULTS FOR SAYAD BAYEZID PORTFOLIO")
        print("="*50)
        print(f"⚡ Performance Score:   {metrics['performance_score']}/100")
        print(f"♿ Accessibility Score: {metrics['accessibility_score']}/100")
        print(f"🔍 SEO Score:           {metrics['seo_score']}/100")
        print("-"*50)
        print("⏱️ CORE WEB VITALS SPLIT:")
        for vital, score in metrics["core_vitals"].items():
            print(f"  • {vital}: {score}")
        
        if metrics["critical_issues"]:
            print("-"*50)
            print("⚠️ DIRECT RENDER BOTTLENECKS FOUND:")
            for issue in metrics["critical_issues"]:
                print(f"  • 🛠️ {issue['issue']} -> {issue['impact']}")
        else:
            print("\n✨ Perfect Score! No critical render issues found.")
        print("="*50)
        print(f"📂 Interactive HTML Report Saved: {metrics['html_report']}\n")
