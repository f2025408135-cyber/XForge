from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Target(Base):
    __tablename__ = "targets"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    tasks = relationship("Task", back_populates="target")
    subdomains = relationship("Subdomain", back_populates="target", cascade="all, delete-orphan")

class Subdomain(Base):
    __tablename__ = "subdomains"
    
    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"))
    hostname = Column(String, nullable=False, index=True)
    ip_address = Column(String, nullable=True)
    
    target = relationship("Target", back_populates="subdomains")
    ports = relationship("Port", back_populates="subdomain", cascade="all, delete-orphan")
    vulnerabilities = relationship("Vulnerability", back_populates="subdomain", cascade="all, delete-orphan")

class Port(Base):
    __tablename__ = "ports"
    
    id = Column(Integer, primary_key=True, index=True)
    subdomain_id = Column(Integer, ForeignKey("subdomains.id"))
    port_number = Column(Integer, nullable=False)
    service = Column(String, nullable=True)
    
    subdomain = relationship("Subdomain", back_populates="ports")

class Vulnerability(Base):
    __tablename__ = "vulnerabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    subdomain_id = Column(Integer, ForeignKey("subdomains.id"))
    template_id = Column(String, nullable=False) # e.g., cve-2021-44228
    severity = Column(String, nullable=False)
    description = Column(String, nullable=True)
    matched_at = Column(String, nullable=False)
    
    subdomain = relationship("Subdomain", back_populates="vulnerabilities")

class DiscoveredEndpoint(Base):
    __tablename__ = "discovered_endpoints"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"))
    method = Column(String, nullable=False)
    path = Column(String, nullable=False)
    parameters = Column(String, nullable=True) # JSON string of discovered query/body params

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"))
    attack_type = Column(String, nullable=False)  # e.g., 'bola', 'sqli'
    status = Column(String, default="PENDING")    # PENDING, RUNNING, COMPLETED, FAILED
    payloads = Column(String, nullable=True)      # Storing JSON string of generated payloads for tracking
    created_at = Column(DateTime, default=datetime.utcnow)

    target = relationship("Target", back_populates="tasks")
    findings = relationship("Finding", back_populates="task", cascade="all, delete-orphan")

class Finding(Base):
    __tablename__ = "findings"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    score = Column(Integer, default=0) # 0 to 100 confidence
    description = Column(String, nullable=True)
    raw_evidence = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    task = relationship("Task", back_populates="findings")
