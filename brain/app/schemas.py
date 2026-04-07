from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# --- Task Schemas ---
class TaskBase(BaseModel):
    attack_type: str

class TaskCreate(TaskBase):
    target_id: int

class FindingBase(BaseModel):
    score: int
    description: Optional[str] = None
    raw_evidence: Optional[str] = None

class Finding(FindingBase):
    id: int
    task_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class Task(TaskBase):
    id: int
    status: str
    payloads: Optional[str] = None
    created_at: datetime
    findings: List[Finding] = []

    class Config:
        from_attributes = True

# --- Recon Schemas ---
class PortBase(BaseModel):
    port_number: int
    service: Optional[str] = None

class Port(PortBase):
    id: int

    class Config:
        from_attributes = True

class VulnerabilityBase(BaseModel):
    template_id: str
    severity: str
    description: Optional[str] = None
    matched_at: str

class Vulnerability(VulnerabilityBase):
    id: int

    class Config:
        from_attributes = True

class SubdomainBase(BaseModel):
    hostname: str
    ip_address: Optional[str] = None

class Subdomain(SubdomainBase):
    id: int
    ports: List[Port] = []
    vulnerabilities: List[Vulnerability] = []

    class Config:
        from_attributes = True

# --- Target Schemas ---
class TargetBase(BaseModel):
    domain: str

class TargetCreate(TargetBase):
    pass

class Target(TargetBase):
    id: int
    is_active: bool
    created_at: datetime
    tasks: List[Task] = []
    subdomains: List[Subdomain] = []

    class Config:
        from_attributes = True
