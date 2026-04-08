from sqlalchemy.orm import Session
from . import models

class ReconParser:
    """
    Ingests and maps JSON outputs from OSS tools into the Database attack graph.
    """
    
    def __init__(self, db: Session, target_id: int):
        self.db = db
        self.target_id = target_id

    def get_or_create_subdomain(self, hostname: str, ip_address: str = None) -> models.Subdomain:
        subdomain = self.db.query(models.Subdomain).filter_by(
            target_id=self.target_id, 
            hostname=hostname
        ).first()

        if not subdomain:
            subdomain = models.Subdomain(
                target_id=self.target_id,
                hostname=hostname,
                ip_address=ip_address
            )
            self.db.add(subdomain)
            self.db.commit()
            self.db.refresh(subdomain)
        elif ip_address and not subdomain.ip_address:
            subdomain.ip_address = ip_address
            self.db.commit()
            
        return subdomain

    def ingest_subfinder(self, results: list):
        """ Parses list of SubfinderResult dicts """
        for res in results:
            host = res.get("host")
            if host:
                self.get_or_create_subdomain(host)

    def ingest_naabu(self, results: list):
        """ Parses list of NaabuResult dicts """
        for res in results:
            host = res.get("host")
            port_num = res.get("port")
            ip = res.get("ip")
            
            if host and port_num:
                sub = self.get_or_create_subdomain(hostname=host, ip_address=ip)
                
                # Check if port exists
                port_exists = self.db.query(models.Port).filter_by(
                    subdomain_id=sub.id, port_number=port_num
                ).first()
                
                if not port_exists:
                    new_port = models.Port(subdomain_id=sub.id, port_number=port_num)
                    self.db.add(new_port)
        
        self.db.commit()

    def ingest_katana(self, results: list):
        """ Parses list of KatanaResult dicts into DiscoveredEndpoints for dynamic spec building """
        from urllib.parse import urlparse, parse_qsl
        import json
        
        for res in results:
            req = res.get("request", {})
            method = req.get("method", "GET")
            endpoint = req.get("endpoint", "")
            body = req.get("body", "")
            
            if not endpoint:
                continue
                
            parsed_url = urlparse(endpoint)
            path = parsed_url.path
            
            # Extract query params
            query_params = [k for k, v in parse_qsl(parsed_url.query)]
            
            # Basic body param extraction
            body_params = []
            if body and (method in ["POST", "PUT", "PATCH"]):
                try:
                    # if it's json
                    body_data = json.loads(body)
                    if isinstance(body_data, dict):
                        body_params = list(body_data.keys())
                except json.JSONDecodeError:
                    # if it's form data
                    body_params = [k for k, v in parse_qsl(body)]

            all_params = list(set(query_params + body_params))
            
            # Deduplicate by path and method
            from .models import DiscoveredEndpoint
            exists = self.db.query(DiscoveredEndpoint).filter_by(
                target_id=self.target_id,
                method=method,
                path=path
            ).first()
            
            if not exists:
                new_ep = DiscoveredEndpoint(
                    target_id=self.target_id,
                    method=method,
                    path=path,
                    parameters=json.dumps(all_params) if all_params else None
                )
                self.db.add(new_ep)
            else:
                # Merge parameters if new ones found
                if all_params:
                    existing_params = []
                    if exists.parameters:
                        existing_params = json.loads(exists.parameters)
                    merged = list(set(existing_params + all_params))
                    exists.parameters = json.dumps(merged)
                    
        self.db.commit()

    def ingest_nuclei(self, results: list):
        """ Parses list of NucleiResult dicts """
        for res in results:
            host = res.get("host")
            # nuclei sometimes outputs full urls in 'host', so we strip to hostname roughly
            # in a real app, use urlparse. We keep it simple here.
            clean_host = host.split("://")[-1].split("/")[0] if host else ""
            
            if clean_host:
                sub = self.get_or_create_subdomain(clean_host)
                
                template_id = res.get("template-id")
                info = res.get("info", {})
                severity = info.get("severity", "unknown")
                name = info.get("name", "")
                matched_at = res.get("matched-at", host)
                
                # Deduplicate by template_id and matched_at
                vuln_exists = self.db.query(models.Vulnerability).filter_by(
                    subdomain_id=sub.id, 
                    template_id=template_id,
                    matched_at=matched_at
                ).first()
                
                if not vuln_exists:
                    vuln = models.Vulnerability(
                        subdomain_id=sub.id,
                        template_id=template_id,
                        severity=severity,
                        description=name,
                        matched_at=matched_at
                    )
                    self.db.add(vuln)

        self.db.commit()
