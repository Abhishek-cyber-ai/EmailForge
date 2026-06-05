#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║     ███████╗███╗   ███╗ █████╗ ██╗██╗         ██████╗ ███████╗██╗███╗   ██╗████████╗
║     ██╔════╝████╗ ████║██╔══██╗██║██║        ██╔══██╗██╔════╝██║████╗  ██║╚══██╔══╝
║     █████╗  ██╔████╔██║███████║██║██║        ██████╔╝███████╗██║██╔██╗ ██║   ██║   
║     ██╔══╝  ██║╚██╔╝██║██╔══██║██║██║        ██╔══██╗╚════██║██║██║╚██╗██║   ██║   
║     ███████╗██║ ╚═╝ ██║██║  ██║██║███████╗    ██║  ██║███████║██║██║ ╚████║   ██║   
║     ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚══════╝    ╚═╝  ╚═╝╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝   
║                                                                               ║
║              Email Intelligence & Pattern Discovery Suite Pro                 ║
║                    Author: Abhishek Rampariya | Version: 9.0                   ║
║                                                                               ║
║   [LAB USE ONLY] Advanced email pattern analysis & intelligent enumeration   ║
║   Features: Pattern learning, Role detection, Team clustering, LinkedIn hints║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import re
import os
import json
import hashlib
import random
import logging
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Set, Dict, Tuple, Optional, Any
from collections import defaultdict, Counter
from itertools import product
import concurrent.futures

# Networking libraries
import dns.resolver
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# For better HTTP handling
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------
CONFIG = {
    "app_name": "Email Intelligence Suite Pro",
    "author": "Avinash Prajapati",
    "version": "9.0",
    "output_dir": "email_intel_reports",
    "log_file": "email_intel.log",
    "max_threads": 15,
    "rate_limit": 0.5,
    "http_timeout": 10,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "max_emails_to_generate": 5000,
    "confidence_threshold": 60,  # Minimum confidence score to show
}

os.makedirs(CONFIG["output_dir"], exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(CONFIG["output_dir"], CONFIG["log_file"])),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# DATA MODELS
# -----------------------------------------------------------------------------
@dataclass
class EmailPattern:
    pattern_type: str  # first.last, firstinitial.last, etc.
    separator: str     # ., _, -, or empty
    capitalization: str # lower, upper, title
    confidence: float
    examples: List[str] = field(default_factory=list)

@dataclass
class PersonInfo:
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    confidence_score: float = 0.0
    source: str = "generated"
    linkedin_hint: Optional[str] = None
    team: Optional[str] = None
    is_verified: bool = False

@dataclass
class RolePattern:
    role: str
    patterns: List[str]
    confidence: float

# -----------------------------------------------------------------------------
# ROLE & DEPARTMENT DETECTION
# -----------------------------------------------------------------------------
class RoleDetector:
    """Detect roles and departments from email addresses"""
    
    ROLE_KEYWORDS = {
        "admin": ["admin", "administrator", "sysadmin", "itadmin", "root"],
        "executive": ["ceo", "cfo", "cto", "coo", "cmo", "cso", "president", "chairman", "founder", "owner"],
        "management": ["director", "manager", "head", "lead", "supervisor", "coordinator"],
        "hr": ["hr", "human", "resources", "recruitment", "recruiter", "talent", "people"],
        "it": ["it", "tech", "technical", "support", "helpdesk", "sysadmin", "network", "devops", "engineer"],
        "sales": ["sales", "business", "bd", "account", "executive", "development", "partnership"],
        "marketing": ["marketing", "mark", "pr", "public", "communications", "social", "content", "seo"],
        "finance": ["finance", "accounting", "accounts", "payroll", "billing", "treasury", "tax"],
        "legal": ["legal", "law", "compliance", "regulatory", "ip", "patent", "attorney"],
        "support": ["support", "help", "service", "customer", "care", "success"],
        "engineering": ["engineering", "eng", "dev", "developer", "software", "qa", "quality"],
        "operations": ["operations", "ops", "facilities", "logistics", "supply", "chain"],
        "research": ["research", "rd", "scientist", "analyst", "data", "ai", "ml"],
        "product": ["product", "pm", "project", "program", "delivery"],
    }
    
    DEPARTMENT_KEYWORDS = {
        "Engineering": ["eng", "dev", "tech", "software", "backend", "frontend", "fullstack"],
        "Sales": ["sales", "bd", "account", "growth"],
        "Marketing": ["marketing", "pr", "comms", "brand"],
        "HR": ["hr", "talent", "recruiting", "people"],
        "Finance": ["finance", "accounting", "fpanda"],
        "Legal": ["legal", "compliance", "risk"],
        "Operations": ["ops", "operations", "facilities"],
        "Product": ["product", "pm", "project"],
        "IT": ["it", "infrastructure", "security"],
        "Support": ["support", "help", "customer"],
    }
    
    @classmethod
    def detect_role(cls, email: str, local_part: str = None) -> Tuple[Optional[str], float]:
        """Detect role from email address"""
        if local_part is None:
            local_part = email.split('@')[0].lower()
        
        local_part_lower = local_part.lower()
        
        for role, keywords in cls.ROLE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in local_part_lower:
                    # Calculate confidence based on match quality
                    confidence = 0.7
                    if local_part_lower == keyword:
                        confidence = 0.95
                    elif local_part_lower.startswith(keyword) or local_part_lower.endswith(keyword):
                        confidence = 0.85
                    return role, confidence
        
        return None, 0.0
    
    @classmethod
    def detect_department(cls, local_part: str) -> Optional[str]:
        """Detect department from email"""
        local_part_lower = local_part.lower()
        
        for dept, keywords in cls.DEPARTMENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in local_part_lower:
                    return dept
        
        return None
    
    @classmethod
    def get_role_confidence(cls, email: str) -> float:
        """Get confidence score for role detection"""
        role, confidence = cls.detect_role(email)
        return confidence

# -----------------------------------------------------------------------------
# EMAIL PATTERN ANALYZER (Learns from existing emails)
# -----------------------------------------------------------------------------
class PatternAnalyzer:
    """Learn email patterns from existing emails and generate new ones"""
    
    def __init__(self, domain: str):
        self.domain = domain
        self.patterns = []
        self.name_variations = {}
        self.common_separators = ['.', '_', '-', '']
        self.common_formats = []
        
    def analyze_email(self, email: str, first_name: str = None, last_name: str = None):
        """Analyze an email to learn pattern"""
        local_part = email.split('@')[0]
        
        # Try to extract name if not provided
        if not first_name or not last_name:
            first_name, last_name = self.extract_name_from_email(local_part)
        
        if first_name and last_name:
            pattern = self.identify_pattern(local_part, first_name, last_name)
            if pattern:
                self.patterns.append(pattern)
    
    def extract_name_from_email(self, local_part: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract potential first/last name from email"""
        # Try common patterns
        patterns = [
            (r'^([a-z]+)\.([a-z]+)$', 1, 2),  # first.last
            (r'^([a-z]+)_([a-z]+)$', 1, 2),  # first_last
            (r'^([a-z]+)-([a-z]+)$', 1, 2),  # first-last
            (r'^([a-z])([a-z]+)$', 1, 2),    # flast
            (r'^([a-z]+)([a-z])$', 1, 2),    # firstl
        ]
        
        for pattern, first_idx, last_idx in patterns:
            match = re.match(pattern, local_part.lower())
            if match:
                first = match.group(first_idx)
                last = match.group(last_idx)
                if len(first) >= 2 and len(last) >= 2:
                    return first, last
        
        return None, None
    
    def identify_pattern(self, local_part: str, first_name: str, last_name: str) -> Optional[EmailPattern]:
        """Identify the pattern used in an email"""
        first = first_name.lower()
        last = last_name.lower()
        f = first[0]
        l = last[0]
        
        pattern_templates = {
            f"{first}.{last}": ("first.last", ".", "lower"),
            f"{first}_{last}": ("first_last", "_", "lower"),
            f"{first}-{last}": ("first-last", "-", "lower"),
            f"{first}{last}": ("firstlast", "", "lower"),
            f"{f}.{last}": ("f.last", ".", "lower"),
            f"{f}_{last}": ("f_last", "_", "lower"),
            f"{f}{last}": ("flast", "", "lower"),
            f"{first}.{l}": ("first.l", ".", "lower"),
            f"{first}{l}": ("firstl", "", "lower"),
            f"{last}.{first}": ("last.first", ".", "lower"),
            f"{last}{first}": ("lastfirst", "", "lower"),
        }
        
        for variant, (pattern_type, separator, case) in pattern_templates.items():
            if local_part.lower() == variant:
                return EmailPattern(
                    pattern_type=pattern_type,
                    separator=separator,
                    capitalization=case,
                    confidence=1.0,
                    examples=[local_part]
                )
        
        return None
    
    def get_common_patterns(self) -> List[EmailPattern]:
        """Get most common patterns with confidence scores"""
        if not self.patterns:
            return []
        
        pattern_counts = Counter([(p.pattern_type, p.separator) for p in self.patterns])
        total = len(self.patterns)
        
        common = []
        for (pattern_type, separator), count in pattern_counts.most_common(3):
            confidence = count / total
            common.append(EmailPattern(
                pattern_type=pattern_type,
                separator=separator,
                capitalization="lower",
                confidence=confidence
            ))
        
        return common

# -----------------------------------------------------------------------------
# INTELLIGENT EMAIL GENERATOR (No sample data, pure pattern-based)
# -----------------------------------------------------------------------------
class IntelligentEmailGenerator:
    """Generate emails using learned patterns and common name lists"""
    
    # Common first names for enumeration (for lab testing)
    COMMON_FIRST_NAMES = [
        "john", "james", "robert", "michael", "william", "david", "richard", "joseph", "thomas", "charles",
        "mary", "patricia", "jennifer", "linda", "elizabeth", "barbara", "susan", "jessica", "sarah", "karen",
        "mohammed", "wei", "alejandro", "maria", "jose", "ahmed", "ali", "fatima", "carlos", "anna"
    ]
    
    # Common last names for enumeration
    COMMON_LAST_NAMES = [
        "smith", "johnson", "williams", "brown", "jones", "garcia", "miller", "davis", "rodriguez", "martinez",
        "hernandez", "lopez", "gonzalez", "wilson", "anderson", "thomas", "taylor", "moore", "jackson", "martin",
        "khan", "singh", "kumar", "zhang", "li", "wang", "kim", "lee", "patel", "sharma"
    ]
    
    # Role-based prefixes
    ROLE_PREFIXES = {
        "admin": ["admin", "administrator"],
        "hr": ["hr", "human.resources", "recruitment"],
        "it": ["it", "tech", "support"],
        "sales": ["sales", "business"],
        "marketing": ["marketing", "social"],
        "finance": ["finance", "accounting"],
        "legal": ["legal", "compliance"],
        "executive": ["ceo", "cfo", "cto", "president"],
    }
    
    def __init__(self, domain: str, pattern_analyzer: PatternAnalyzer = None):
        self.domain = domain
        self.pattern_analyzer = pattern_analyzer or PatternAnalyzer(domain)
        self.generated_emails = set()
        
    def generate_from_patterns(self, first_names: List[str] = None, last_names: List[str] = None) -> Set[str]:
        """Generate emails based on learned patterns"""
        if not first_names:
            first_names = self.COMMON_FIRST_NAMES
        if not last_names:
            last_names = self.COMMON_LAST_NAMES
        
        emails = set()
        patterns = self.pattern_analyzer.get_common_patterns()
        
        if not patterns:
            # Default patterns if none learned
            patterns = [
                EmailPattern("first.last", ".", "lower", 0.8),
                EmailPattern("firstlast", "", "lower", 0.7),
                EmailPattern("f.last", ".", "lower", 0.6),
            ]
        
        for first in first_names[:20]:  # Limit for performance
            for last in last_names[:20]:
                for pattern in patterns:
                    email = self._apply_pattern(first, last, pattern)
                    if email:
                        emails.add(email)
        
        return emails
    
    def _apply_pattern(self, first: str, last: str, pattern: EmailPattern) -> Optional[str]:
        """Apply a pattern to generate email"""
        first = first.lower()
        last = last.lower()
        f = first[0]
        l = last[0]
        
        try:
            if pattern.pattern_type == "first.last":
                local = f"{first}{pattern.separator}{last}"
            elif pattern.pattern_type == "first_last":
                local = f"{first}{pattern.separator}{last}"
            elif pattern.pattern_type == "first-last":
                local = f"{first}{pattern.separator}{last}"
            elif pattern.pattern_type == "firstlast":
                local = f"{first}{last}"
            elif pattern.pattern_type == "f.last":
                local = f"{f}{pattern.separator}{last}"
            elif pattern.pattern_type == "f_last":
                local = f"{f}{pattern.separator}{last}"
            elif pattern.pattern_type == "flast":
                local = f"{f}{last}"
            elif pattern.pattern_type == "first.l":
                local = f"{first}{pattern.separator}{l}"
            elif pattern.pattern_type == "firstl":
                local = f"{first}{l}"
            elif pattern.pattern_type == "last.first":
                local = f"{last}{pattern.separator}{first}"
            elif pattern.pattern_type == "lastfirst":
                local = f"{last}{first}"
            else:
                return None
            
            # Apply capitalization
            if pattern.capitalization == "upper":
                local = local.upper()
            elif pattern.capitalization == "title":
                local = local.title()
            
            return f"{local}@{self.domain}"
        except:
            return None
    
    def generate_role_emails(self) -> Set[str]:
        """Generate role-based emails"""
        emails = set()
        
        for role, prefixes in self.ROLE_PREFIXES.items():
            for prefix in prefixes:
                emails.add(f"{prefix}@{self.domain}")
                # Add variations with separators
                for sep in ['.', '_', '-']:
                    emails.add(f"{prefix.replace('.', sep)}@{self.domain}")
        
        return emails
    
    def generate_numerical_variations(self, base_emails: Set[str], max_per_email: int = 5) -> Set[str]:
        """Generate numerical variations of existing emails"""
        variations = set()
        
        for email in base_emails:
            local, domain = email.split('@')
            # Add numbers 1-5
            for num in range(1, max_per_email + 1):
                variations.add(f"{local}{num}@{domain}")
        
        return variations
    
    def smart_generate(self, seed_email: str = None, mode: str = "smart") -> Set[str]:
        """
        Main generation method
        mode: "smart" - learns from patterns, "brute" - comprehensive enumeration
        """
        all_emails = set()
        
        # Always include role emails
        all_emails.update(self.generate_role_emails())
        
        if mode == "smart":
            # Smart mode: Use pattern learning with limited enumeration
            logger.info("Smart mode: Using pattern-based generation")
            pattern_emails = self.generate_from_patterns()
            all_emails.update(pattern_emails)
            
            # Add numerical variations of role emails
            all_emails.update(self.generate_numerical_variations(self.generate_role_emails(), 3))
            
        else:  # brute mode
            # Brute mode: More comprehensive enumeration for lab testing
            logger.info("Brute mode: Comprehensive enumeration")
            
            # Generate from all name combinations
            for first in self.COMMON_FIRST_NAMES[:30]:
                for last in self.COMMON_LAST_NAMES[:30]:
                    # Try multiple patterns
                    patterns_to_try = [
                        f"{first}.{last}",
                        f"{first}_{last}",
                        f"{first}{last}",
                        f"{first[0]}.{last}",
                        f"{first[0]}{last}",
                        f"{first}.{last[0]}",
                        f"{last}.{first}",
                        f"{last}{first}",
                    ]
                    for pattern in patterns_to_try:
                        all_emails.add(f"{pattern}@{self.domain}")
            
            # Add numerical variations
            all_emails.update(self.generate_numerical_variations(all_emails, 3))
        
        return all_emails

# -----------------------------------------------------------------------------
# LINKEDIN PROFILE HINT GENERATOR
# -----------------------------------------------------------------------------
class LinkedInHintGenerator:
    """Generate LinkedIn profile hints based on email patterns"""
    
    @staticmethod
    def generate_hint(first_name: str, last_name: str, company: str) -> str:
        """Generate LinkedIn profile hint"""
        profiles = []
        
        # Common LinkedIn URL patterns
        patterns = [
            f"linkedin.com/in/{first_name.lower()}-{last_name.lower()}",
            f"linkedin.com/in/{first_name.lower()}{last_name.lower()}",
            f"linkedin.com/in/{first_name[0].lower()}{last_name.lower()}",
            f"linkedin.com/company/{company.lower().replace(' ', '-')}",
        ]
        
        return patterns[0]  # Return most likely pattern
    
    @staticmethod
    def search_similar_profiles(name: str, domain: str) -> List[str]:
        """Search for similar profiles (mock for lab testing)"""
        # This would normally use LinkedIn API, but for lab we return patterns
        return [f"https://www.linkedin.com/search/results/people/?keywords={name.replace(' ', '%20')}"]

# -----------------------------------------------------------------------------
# TEAM CLUSTERING & ORGANIZATION DETECTION
# -----------------------------------------------------------------------------
class TeamCluster:
    """Cluster emails into teams/departments"""
    
    def __init__(self):
        self.clusters = defaultdict(list)
        
    def add_email(self, email: str, role: str = None, department: str = None):
        """Add email to appropriate cluster"""
        if role:
            self.clusters[f"role_{role}"].append(email)
        elif department:
            self.clusters[f"dept_{department}"].append(email)
        else:
            # Try to detect from email
            local_part = email.split('@')[0]
            if any(role_word in local_part for role_word in ['sales', 'marketing', 'hr', 'it', 'support']):
                self.clusters["detected_team"].append(email)
            else:
                self.clusters["general"].append(email)
    
    def get_team_summary(self) -> Dict[str, List[str]]:
        """Get summary of teams"""
        return dict(self.clusters)

# -----------------------------------------------------------------------------
# EMAIL VERIFICATION (SMTP)
# -----------------------------------------------------------------------------
class EmailVerifier:
    """Verify email existence via SMTP"""
    
    @staticmethod
    def get_mx_records(domain: str) -> List[str]:
        """Get MX records for domain"""
        try:
            answers = dns.resolver.resolve(domain, 'MX', lifetime=5)
            return [str(r.exchange).rstrip('.') for r in answers]
        except:
            return []
    
    @staticmethod
    def verify_email(email: str, mx_servers: List[str]) -> bool:
        """Verify email via SMTP"""
        if not mx_servers:
            return False
        
        for mx in mx_servers[:2]:
            try:
                import smtplib
                smtp = smtplib.SMTP(mx, timeout=8)
                smtp.ehlo_or_helo_if_needed()
                smtp.mail('verify@test.com')
                code, _ = smtp.rcpt(email)
                smtp.quit()
                return code in (250, 251)
            except:
                continue
        return False
    
    def verify_batch(self, emails: Set[str], max_workers: int = 10, callback=None) -> Dict[str, bool]:
        """Verify multiple emails"""
        results = {}
        domain = list(emails)[0].split('@')[1] if emails else ""
        mx_servers = self.get_mx_records(domain)
        
        if not mx_servers:
            return {email: False for email in emails}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_email = {executor.submit(self.verify_email, email, mx_servers): email for email in emails}
            
            for future in concurrent.futures.as_completed(future_to_email):
                email = future_to_email[future]
                try:
                    results[email] = future.result()
                    if callback:
                        callback(email, results[email])
                except:
                    results[email] = False
        
        return results

# -----------------------------------------------------------------------------
# MAIN GUI APPLICATION
# -----------------------------------------------------------------------------
class EmailIntelDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{CONFIG['app_name']} - {CONFIG['author']}")
        self.root.geometry("1400x850")
        self.root.configure(bg="#0a0a1a")
        
        # Variables
        self.domain_var = tk.StringVar()
        self.seed_email_var = tk.StringVar()
        self.mode_var = tk.StringVar(value="smart")  # smart or brute
        self.max_results_var = tk.IntVar(value=500)
        self.verify_emails_var = tk.BooleanVar(value=True)
        
        self.generated_people = []
        self.verified_emails = set()
        self.running = False
        
        self.setup_styles()
        self.build_ui()
        
    def setup_styles(self):
        self.bg_dark = "#0a0a1a"
        self.bg_sidebar = "#0f0f25"
        self.bg_card = "#1a1a2e"
        self.fg_primary = "#ffffff"
        self.fg_secondary = "#aaaaaa"
        self.accent_smart = "#3498db"
        self.accent_brute = "#e74c3c"
        self.accent_valid = "#2ecc71"
        
    def build_ui(self):
        # Header
        header = tk.Frame(self.root, bg=self.bg_card, height=70)
        header.pack(fill=tk.X)
        tk.Label(header, text="🔍 Email Intelligence & Pattern Discovery Suite", 
                font=("Segoe UI", 16, "bold"), fg=self.accent_smart, bg=self.bg_card).pack(side=tk.LEFT, padx=20, pady=15)
        tk.Label(header, text="[LAB USE ONLY]", font=("Segoe UI", 10, "bold"),
                fg=self.accent_brute, bg=self.bg_card).pack(side=tk.LEFT, padx=10)
        
        # Mode selector in header
        mode_frame = tk.Frame(header, bg=self.bg_card)
        mode_frame.pack(side=tk.RIGHT, padx=20)
        
        tk.Label(mode_frame, text="Mode:", fg=self.fg_primary, bg=self.bg_card).pack(side=tk.LEFT, padx=5)
        
        self.smart_radio = tk.Radiobutton(mode_frame, text="🎯 Smart Mode", variable=self.mode_var, value="smart",
                                         bg=self.bg_card, fg=self.accent_smart, selectcolor=self.bg_card,
                                         activebackground=self.bg_card, activeforeground=self.accent_smart)
        self.smart_radio.pack(side=tk.LEFT, padx=5)
        
        self.brute_radio = tk.Radiobutton(mode_frame, text="⚡ Brute Mode", variable=self.mode_var, value="brute",
                                         bg=self.bg_card, fg=self.accent_brute, selectcolor=self.bg_card,
                                         activebackground=self.bg_card, activeforeground=self.accent_brute)
        self.brute_radio.pack(side=tk.LEFT, padx=5)
        
        # Main container
        main = tk.Frame(self.root, bg=self.bg_dark)
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Left panel - Input & Controls
        left = tk.Frame(main, bg=self.bg_sidebar, width=450)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left.pack_propagate(False)
        
        # Input section
        input_frame = tk.LabelFrame(left, text="📧 Input Configuration", bg=self.bg_sidebar, fg=self.fg_primary,
                                    font=("Segoe UI", 11, "bold"), relief=tk.GROOVE)
        input_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # Domain input
        tk.Label(input_frame, text="Target Domain:", fg=self.fg_primary, bg=self.bg_sidebar,
                font=("Segoe UI", 10)).pack(anchor=tk.W, padx=10, pady=(10,5))
        domain_entry = tk.Entry(input_frame, textvariable=self.domain_var, font=("Segoe UI", 11),
                               bg=self.bg_card, fg="white", insertbackground="white", relief=tk.FLAT)
        domain_entry.pack(fill=tk.X, padx=10, pady=(0,10))
        
        # Seed email (optional)
        tk.Label(input_frame, text="Seed Email (Optional - for pattern learning):", fg=self.fg_primary, 
                bg=self.bg_sidebar, font=("Segoe UI", 10)).pack(anchor=tk.W, padx=10, pady=(5,5))
        seed_entry = tk.Entry(input_frame, textvariable=self.seed_email_var, font=("Segoe UI", 11),
                             bg=self.bg_card, fg="white", insertbackground="white", relief=tk.FLAT)
        seed_entry.pack(fill=tk.X, padx=10, pady=(0,10))
        
        # Options
        options_frame = tk.LabelFrame(left, text="⚙️ Generation Options", bg=self.bg_sidebar, fg=self.fg_primary,
                                      font=("Segoe UI", 11, "bold"), relief=tk.GROOVE)
        options_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # Max results slider
        tk.Label(options_frame, text=f"Max Results: {self.max_results_var.get()}", 
                fg=self.fg_primary, bg=self.bg_sidebar).pack(anchor=tk.W, padx=10, pady=5)
        max_slider = ttk.Scale(options_frame, from_=50, to=2000, orient=tk.HORIZONTAL,
                              variable=self.max_results_var, length=380)
        max_slider.pack(padx=10, pady=5)
        max_slider.configure(command=lambda x: self.update_max_label())
        
        # Verify checkbox
        tk.Checkbutton(options_frame, text="Verify emails via SMTP (slower but accurate)", 
                      variable=self.verify_emails_var, bg=self.bg_sidebar, fg=self.fg_primary,
                      selectcolor=self.bg_sidebar).pack(anchor=tk.W, padx=10, pady=5)
        
        # Start button
        self.start_btn = tk.Button(left, text="🚀 START DISCOVERY", command=self.start_discovery,
                                  bg=self.accent_smart, fg="white", font=("Segoe UI", 12, "bold"),
                                  relief=tk.FLAT, padx=20, pady=10, cursor="hand2")
        self.start_btn.pack(pady=20, padx=15, fill=tk.X)
        
        # Progress
        self.progress_bar = ttk.Progressbar(left, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.progress_bar.pack(pady=5, padx=15)
        self.progress_label = tk.Label(left, text="Ready", fg=self.fg_secondary, bg=self.bg_sidebar)
        self.progress_label.pack()
        
        # Right panel - Results
        right = tk.Frame(main, bg=self.bg_dark)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Results notebook (tabs)
        self.notebook = ttk.Notebook(right)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Discovered People
        self.people_frame = tk.Frame(self.notebook, bg=self.bg_dark)
        self.notebook.add(self.people_frame, text="👥 Discovered People")
        self.setup_people_tab()
        
        # Tab 2: Teams & Clusters
        self.teams_frame = tk.Frame(self.notebook, bg=self.bg_dark)
        self.notebook.add(self.teams_frame, text="🏢 Teams & Clusters")
        self.setup_teams_tab()
        
        # Tab 3: Patterns Learned
        self.patterns_frame = tk.Frame(self.notebook, bg=self.bg_dark)
        self.notebook.add(self.patterns_frame, text="📊 Patterns Learned")
        self.setup_patterns_tab()
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN,
                             anchor=tk.W, bg=self.bg_card, fg=self.fg_secondary)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Log area
        log_frame = tk.Frame(self.root, bg=self.bg_dark, height=120)
        log_frame.pack(fill=tk.X, padx=15, pady=(0,10))
        tk.Label(log_frame, text="📋 Activity Log:", fg=self.fg_secondary, bg=self.bg_dark).pack(anchor=tk.W)
        self.log_text = tk.Text(log_frame, height=5, font=("Consolas", 9), bg=self.bg_card,
                                fg="#cccccc", relief=tk.FLAT, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
    def setup_people_tab(self):
        # Treeview for people
        columns = ("Email", "Role", "Department", "Confidence", "LinkedIn Hint")
        self.people_tree = ttk.Treeview(self.people_frame, columns=columns, show="headings", height=20)
        
        for col in columns:
            self.people_tree.heading(col, text=col)
            self.people_tree.column(col, width=150 if col != "LinkedIn Hint" else 250)
        
        scrollbar = ttk.Scrollbar(self.people_frame, orient=tk.VERTICAL, command=self.people_tree.yview)
        self.people_tree.configure(yscrollcommand=scrollbar.set)
        
        self.people_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10,0), pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,10), pady=10)
        
    def setup_teams_tab(self):
        self.teams_text = tk.Text(self.teams_frame, bg=self.bg_card, fg=self.fg_primary,
                                  font=("Consolas", 10), wrap=tk.WORD, relief=tk.FLAT)
        self.teams_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def setup_patterns_tab(self):
        self.patterns_text = tk.Text(self.patterns_frame, bg=self.bg_card, fg=self.fg_primary,
                                     font=("Consolas", 10), wrap=tk.WORD, relief=tk.FLAT)
        self.patterns_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def update_max_label(self):
        # Update label when slider moves
        pass
    
    def log(self, msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        logger.info(msg)
    
    def start_discovery(self):
        if self.running:
            return
        
        domain = self.domain_var.get().strip()
        if not domain:
            messagebox.showerror("Error", "Please enter target domain")
            return
        
        # Clean domain
        domain = re.sub(r'^https?://', '', domain)
        domain = re.sub(r'/.*$', '', domain)
        domain = domain.lower()
        
        self.running = True
        self.start_btn.config(state=tk.DISABLED, text="RUNNING...")
        self.progress_bar['value'] = 0
        
        # Clear previous results
        for item in self.people_tree.get_children():
            self.people_tree.delete(item)
        self.teams_text.delete(1.0, tk.END)
        self.patterns_text.delete(1.0, tk.END)
        
        thread = threading.Thread(target=self._run_discovery, args=(domain,), daemon=True)
        thread.start()
    
    def _run_discovery(self, domain: str):
        try:
            # Step 1: Initialize pattern analyzer
            self.log(f"🎯 Target domain: {domain}")
            self.log(f"🔧 Mode: {self.mode_var.get().upper()}")
            
            pattern_analyzer = PatternAnalyzer(domain)
            
            # If seed email provided, learn from it
            seed_email = self.seed_email_var.get().strip()
            if seed_email and '@' in seed_email:
                self.log(f"📧 Learning patterns from seed email: {seed_email}")
                local_part = seed_email.split('@')[0]
                first, last = pattern_analyzer.extract_name_from_email(local_part)
                if first and last:
                    pattern_analyzer.analyze_email(seed_email, first, last)
                    self.log(f"✅ Learned pattern from {first}.{last}")
            
            # Step 2: Generate emails
            self.log("🔄 Generating email addresses...")
            generator = IntelligentEmailGenerator(domain, pattern_analyzer)
            generated_emails = generator.smart_generate(seed_email, mode=self.mode_var.get())
            
            # Limit results
            max_results = self.max_results_var.get()
            generated_emails = list(generated_emails)[:max_results]
            self.log(f"📊 Generated {len(generated_emails)} unique email addresses")
            
            # Step 3: Analyze each email
            self.log("🔍 Analyzing emails for roles and patterns...")
            people = []
            total = len(generated_emails)
            
            for i, email in enumerate(generated_emails):
                local_part = email.split('@')[0]
                
                # Detect role and department
                role, role_conf = RoleDetector.detect_role(email, local_part)
                department = RoleDetector.detect_department(local_part)
                
                # Calculate confidence score
                confidence = role_conf if role_conf > 0 else 0.5
                if department:
                    confidence += 0.1
                
                # Extract potential name
                first, last = pattern_analyzer.extract_name_from_email(local_part)
                
                # Generate LinkedIn hint
                linkedin_hint = None
                if first and last:
                    linkedin_hint = LinkedInHintGenerator.generate_hint(first, last, domain.split('.')[0])
                
                person = PersonInfo(
                    email=email,
                    first_name=first,
                    last_name=last,
                    role=role,
                    department=department,
                    confidence_score=min(confidence, 1.0),
                    source="generated",
                    linkedin_hint=linkedin_hint
                )
                people.append(person)
                
                # Update progress
                if i % 100 == 0:
                    self.progress_bar['value'] = (i / total) * 50
                    self.progress_label.config(text=f"Analyzing {i}/{total}")
                    self.root.update_idletasks()
            
            # Step 4: Verify emails if requested
            if self.verify_emails_var.get():
                self.log("✅ Verifying emails via SMTP (this may take a moment)...")
                verifier = EmailVerifier()
                email_set = {p.email for p in people}
                
                def verify_callback(email, is_valid):
                    if is_valid:
                        self.verified_emails.add(email)
                
                verification_results = verifier.verify_batch(email_set, max_workers=10, callback=verify_callback)
                
                # Update people with verification status
                for person in people:
                    person.is_verified = verification_results.get(person.email, False)
                
                self.log(f"✅ Verification complete: {len(self.verified_emails)} valid emails found")
            
            # Step 5: Display results
            self.progress_bar['value'] = 75
            self.progress_label.config(text="Displaying results...")
            
            # Sort by confidence
            people.sort(key=lambda x: x.confidence_score, reverse=True)
            self.generated_people = people
            
            # Display in tree
            for person in people[:max_results]:
                if person.confidence_score >= CONFIG["confidence_threshold"] / 100:
                    verified_mark = "✅ " if person.is_verified else ""
                    role_text = person.role or "Unknown"
                    dept_text = person.department or "-"
                    confidence_pct = f"{person.confidence_score*100:.0f}%"
                    linkedin_hint = person.linkedin_hint or "-"
                    
                    self.people_tree.insert("", tk.END, values=(
                        f"{verified_mark}{person.email}",
                        role_text,
                        dept_text,
                        confidence_pct,
                        linkedin_hint
                    ))
            
            # Step 6: Team clustering
            self.log("🏢 Creating team clusters...")
            cluster = TeamCluster()
            for person in people:
                cluster.add_email(person.email, person.role, person.department)
            
            teams_summary = cluster.get_team_summary()
            self.teams_text.insert(tk.END, "🏢 TEAM CLUSTERS\n")
            self.teams_text.insert(tk.END, "="*50 + "\n\n")
            
            for team, members in teams_summary.items():
                self.teams_text.insert(tk.END, f"📌 {team.upper()} ({len(members)} members)\n")
                self.teams_text.insert(tk.END, "-"*40 + "\n")
                for member in members[:10]:  # Show first 10
                    self.teams_text.insert(tk.END, f"  • {member}\n")
                if len(members) > 10:
                    self.teams_text.insert(tk.END, f"  ... and {len(members)-10} more\n")
                self.teams_text.insert(tk.END, "\n")
            
            # Step 7: Show learned patterns
            self.patterns_text.insert(tk.END, "📊 EMAIL PATTERNS LEARNED\n")
            self.patterns_text.insert(tk.END, "="*50 + "\n\n")
            
            patterns = pattern_analyzer.get_common_patterns()
            if patterns:
                for pattern in patterns:
                    self.patterns_text.insert(tk.END, f"🔹 Pattern: {pattern.pattern_type}\n")
                    self.patterns_text.insert(tk.END, f"   Separator: '{pattern.separator}'\n")
                    self.patterns_text.insert(tk.END, f"   Confidence: {pattern.confidence*100:.1f}%\n")
                    if pattern.examples:
                        self.patterns_text.insert(tk.END, f"   Examples: {', '.join(pattern.examples)}\n")
                    self.patterns_text.insert(tk.END, "\n")
            else:
                self.patterns_text.insert(tk.END, "No patterns learned yet. Provide a seed email to learn patterns.\n")
            
            # Final summary
            valid_count = len([p for p in people if p.is_verified])
            self.log(f"\n{'='*50}")
            self.log(f"📊 DISCOVERY COMPLETE")
            self.log(f"{'='*50}")
            self.log(f"Total emails generated: {len(people)}")
            self.log(f"Valid emails found: {valid_count}")
            self.log(f"Roles detected: {len([p for p in people if p.role])}")
            self.log(f"Teams identified: {len(teams_summary)}")
            
            # Save report
            self.save_report(domain, people, teams_summary, patterns)
            
        except Exception as e:
            self.log(f"❌ Error: {e}")
            logger.exception("Discovery error")
        finally:
            self._finish_run()
    
    def save_report(self, domain: str, people: List[PersonInfo], teams: Dict, patterns: List):
        """Save detailed report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON
        report = {
            "domain": domain,
            "timestamp": timestamp,
            "mode": self.mode_var.get(),
            "total_discovered": len(people),
            "valid_emails": len([p for p in people if p.is_verified]),
            "people": [asdict(p) for p in people if p.confidence_score >= 0.5],
            "teams": {k: v for k, v in teams.items()},
            "patterns": [asdict(p) for p in patterns] if patterns else []
        }
        
        json_path = os.path.join(CONFIG["output_dir"], f"{domain}_{timestamp}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.log(f"💾 Report saved: {json_path}")
        
        # Save text report
        txt_path = os.path.join(CONFIG["output_dir"], f"{domain}_{timestamp}.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"Email Intelligence Report - {domain}\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write(f"Mode: {self.mode_var.get()}\n")
            f.write("="*60 + "\n\n")
            
            f.write("VALID EMAILS FOUND\n")
            f.write("-"*40 + "\n")
            for person in people:
                if person.is_verified:
                    f.write(f"✅ {person.email}")
                    if person.role:
                        f.write(f" [{person.role}]")
                    if person.department:
                        f.write(f" ({person.department})")
                    f.write(f" - Confidence: {person.confidence_score*100:.0f}%\n")
            
            f.write(f"\nTotal: {len([p for p in people if p.is_verified])} valid emails\n")
        
        self.log(f"📄 Text report saved: {txt_path}")
    
    def _finish_run(self):
        self.running = False
        self.start_btn.config(state=tk.NORMAL, text="🚀 START DISCOVERY")
        self.progress_bar['value'] = 100
        self.progress_label.config(text="Complete")
        self.status_var.set("Ready")
        self.log("✅ Discovery completed successfully!")

# -----------------------------------------------------------------------------
# MAIN ENTRY POINT
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = EmailIntelDashboard(root)
    root.mainloop()