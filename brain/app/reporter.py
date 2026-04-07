from sqlalchemy.orm import Session
from datetime import datetime
from .models import Target, Subdomain, Port, Vulnerability, Task, Finding

class ReportGenerator:
    """
    Compiles all gathered intelligence (Recon, Vulnerabilities, and Fuzzing Findings)
    into a structured Markdown report for a specific target.
    """
    def __init__(self, db: Session):
        self.db = db

    def generate_markdown_report(self, target_id: int) -> str:
        target = self.db.query(Target).filter(Target.id == target_id).first()
        if not target:
            return "Error: Target not found."

        report = []
        report.append(f"# XForge Autonomous Security Report: {target.domain}")
        report.append(f"*Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*\\n")

        # --- Section 1: Reconnaissance Data ---
        report.append("## 1. Attack Surface Mapping")
        
        subdomains = self.db.query(Subdomain).filter(Subdomain.target_id == target_id).all()
        if not subdomains:
            report.append("> No subdomains discovered.")
        else:
            for sub in subdomains:
                ip_str = f" ({sub.ip_address})" if sub.ip_address else ""
                report.append(f"### {sub.hostname}{ip_str}")
                
                ports = self.db.query(Port).filter(Port.subdomain_id == sub.id).all()
                if ports:
                    port_list = ", ".join([str(p.port_number) for p in ports])
                    report.append(f"- **Open Ports:** {port_list}")
                
                vulns = self.db.query(Vulnerability).filter(Vulnerability.subdomain_id == sub.id).all()
                if vulns:
                    report.append("- **Known Vulnerabilities (Nuclei):**")
                    for v in vulns:
                        report.append(f"  - [{v.severity.upper()}] {v.template_id}: {v.description} (Matched at: {v.matched_at})")
                report.append("")

        # --- Section 2: Active Fuzzing Findings ---
        report.append("\\n## 2. Autonomous Exploitation Findings")
        
        tasks = self.db.query(Task).filter(Task.target_id == target_id).all()
        has_findings = False
        
        for task in tasks:
            findings = self.db.query(Finding).filter(Finding.task_id == task.id).all()
            for finding in findings:
                if finding.score > 0:  # Only report actual anomalies/vulnerabilities
                    has_findings = True
                    report.append(f"### {task.attack_type.upper()} Vulnerability Detected (Confidence: {finding.score*100}%)")
                    report.append(f"**Description:** {finding.description}")
                    
                    if finding.raw_evidence:
                        report.append(f"\\n**Proof of Concept:**")
                        report.append(f"```bash\\n{finding.raw_evidence}\\n```")
                    report.append("---\\n")

        if not has_findings:
            report.append("> No active exploitation anomalies detected during this run.")

        return "\\n".join(report)
