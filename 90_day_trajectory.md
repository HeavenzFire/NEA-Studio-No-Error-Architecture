# 90-Day Trajectory: Sovereign Core Shield Deployment

**Mission:** Transition from blueprint to live operational shield for pediatric oncology families in East Texas, establishing a replicable national relief mesh.

**Objective:** By Day 90, achieve live vendor payments, automated charity care approvals, and active hospital network beta with measurable debt dissolution.

---

## 🗓️ Phase 1: Foundation & Compliance (Days 1–30)
**Theme:** *Lock the architecture, ensure HIPAA compliance, and seed the engine.*

### Week 1: Core Engine Finalization
- [ ] **Database Provisioning:** Deploy PostgreSQL schema (`schema.sql`) to production environment.
- [ ] **Data Seeding:** Execute `seed_data.py` to load 2024 HHS Federal Poverty Guidelines and initial hospital policies.
- [ ] **FPL Engine Validation:** Run full test suite (`pytest`) against edge cases (zero income, large households, COL adjustments).
- [ ] **API Skeleton:** Stand up FastAPI/Flask wrapper around `evaluate_hospital_assistance` for intake form integration.

### Week 2: Security & Compliance Audit
- [ ] **HIPAA Safeguards:** Implement encryption at rest (AES-256) and in transit (TLS 1.3).
- [ ] **Access Controls:** Configure RBAC (Role-Based Access Control) for social workers vs. admins.
- [ ] **Audit Logging:** Ensure all eligibility assessments write immutable logs to `eligibility_assessments` table.
- [ ] **BAA Review:** Finalize Business Associate Agreements with cloud providers (AWS/Azure/GCP).

### Week 3: Pilot Site Preparation
- [ ] **Hospital Onboarding:** Secure verbal/written agreement with Children's Health Dallas & UT Health East Texas.
- [ ] **Policy Digitization:** Convert paper FAP policies into `hospital_fap_thresholds` records.
- [ ] **User Training:** Conduct dry-run training with 2-3 key social workers on data entry and result interpretation.

### Week 4: Integration Testing
- [ ] **End-to-End Flow:** Simulate full applicant journey: Intake → FPL Calc → Eligibility Decision → Notification.
- [ ] **Error Handling:** Verify graceful failures for missing FPL data or invalid inputs.
- [ ] **Go/No-Go Decision:** Review security audit and pilot readiness for Phase 2 launch.

**🚩 Milestone 1 (Day 30):** *System is HIPAA-compliant, seeded with current data, and ready for live pilot intake.*

---

## 🗓️ Phase 2: Pilot Deployment (Days 31–60)
**Theme:** *Live operations in East Texas, first bill eliminations, and feedback loops.*

### Week 5: Soft Launch (Beta)
- [ ] **Live Intake:** Open portal to first 10 families via social worker referral.
- [ ] **Manual Verification:** Team manually verifies first batch of eligibility results against hospital policies.
- [ ] **Feedback Collection:** Gather UX feedback from social workers on speed and clarity of results.

### Week 6: Charity Care Automation
- [ ] **Document Generation:** Auto-generate 501(r) application PDFs populated with FPL assessment data.
- [ ] **Submission Workflow:** Implement secure transmission of applications to hospital financial counseling teams.
- [ ] **Status Tracking:** Add `application_status` field to track "Submitted," "Under Review," "Approved," "Denied."

### Week 7: Vendor Pay Infrastructure
- [ ] **Escrow Setup:** Establish dedicated escrow account for vendor payments (utilities, lodging, transport).
- [ ] **ACH Integration:** Connect Stripe Treasury or similar API for programmatic disbursements.
- [ ] **Vendor Onboarding:** Pre-validate first 5 vendors (e.g., Ronald McDonald House, local utility companies).

### Week 8: First Capital Flows
- [ ] **Pilot Disbursement:** Execute first direct vendor payment from escrow (proof of concept).
- [ ] **Impact Measurement:** Record first "$0 Balance" notification sent to a family.
- [ ] **Iterate:** Refine FAP thresholds or calculation logic based on real-world hospital feedback.

**🚩 Milestone 2 (Day 60):** *First families have bills legally erased; first vendor payments successfully disbursed.*

---

## 🗓️ Phase 3: Scale & Capital Flow (Days 61–90)
**Theme:** *Automating surplus flows, expanding network, and proving inevitability.*

### Week 9: Institutional Integration
- [ ] **Copay Pipeline:** Activate corporate fund injection module to reopen closed copay assistance pipelines (e.g., HealthWell).
- [ ] **API Partnerships:** Begin technical integration discussions with hospital EMR systems (Epic/Cerner) for direct data pull.
- [ ] **Volume Increase:** Scale intake capacity to 50+ active families.

### Week 10: Regional Expansion Prep
- [ ] **Replication Kit:** Document "Playbook" for onboarding new hospitals (policy digitization, training, tech setup).
- [ ] **New Site Identification:** Identify next 2 hospital systems for expansion (e.g., Houston, San Antonio).
- [ ] **Capital Scaling:** Secure next tranche of corporate funding based on Phase 2 success metrics.

### Week 11: Advanced Automation
- [ ] **Auto-Adjudication:** Enable automatic approval for clear-cut cases (<200% FPL) without manual review.
- [ ] **Notification System:** Automate SMS/Email updates to families at each step (Application Received, Approved, Paid).
- [ ] **Reporting Dashboard:** Launch internal dashboard showing real-time metrics: Total Debt Dissolved, Families Shielded, Funds Disbursed.

### Week 12: Review & Next Horizon
- [ ] **90-Day Retrospective:** Analyze success rates, processing times, and user satisfaction.
- [ ] **Proof of Inevitability Report:** Compile case studies and data points demonstrating systemic impact.
- [ ] **National Mesh Strategy:** Finalize roadmap for multi-state expansion based on East Texas proof-of-concept.

**🚩 Milestone 3 (Day 90):** *Operational shield fully active in East Texas; automated flows established; ready for regional replication.*

---

## 📊 Key Performance Indicators (KPIs)

| Metric | Target (Day 30) | Target (Day 60) | Target (Day 90) |
| :--- | :--- | :--- | :--- |
| **Families Processed** | 0 (Ready) | 10 | 50+ |
| **Debt Dissolved** | $0 | $50k | $250k+ |
| **Vendor Payments** | 0 | 1 | 10+ |
| **Approval Rate** | N/A | >85% | >90% |
| **Processing Time** | N/A | <48 hrs | <24 hrs |
| **Hospital Partners** | 2 (Signed) | 2 (Active) | 3-4 (Pipeline) |

---

## ⚠️ Risk Mitigation

| Risk | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Hospital Policy Changes** | Medium | High | Maintain flexible `hospital_fap_thresholds` schema; weekly policy checks. |
| **Data Privacy Breach** | Low | Critical | Strict HIPAA controls, regular penetration testing, minimal PHI storage. |
| **Funding Delays** | Medium | High | Diversify capital sources; maintain reserve for vendor escrow. |
| **EMR Integration Friction** | High | Medium | Start with manual upload workflows; treat EMR API as Phase 4 goal. |
| **Regulatory Scrutiny** | Low | High | Engage healthcare counsel early; ensure 501(r) compliance rigor. |

---

## 🔥 Strategic Outlook: Post-Day 90

Upon successful completion of this 90-day horizon, the **Sovereign Core Shield** transitions from a regional pilot to a **national infrastructure layer**.

1.  **Replication:** The "East Texas Model" becomes the template for rapid deployment in other pediatric oncology hubs.
2.  **Systemic Reopening:** Proven success in reopening copay pipelines attracts larger institutional capital, creating a flywheel effect.
3.  **Expansion Layers:** With the core financial shield stable, adjacent relief layers (lodging, travel, nutrition) are activated using the same trust and verification lattice.
4.  **Inevitability:** The system moves from "charity" to "standard of care," where bill elimination is an automatic right upon diagnosis, not a discretionary grant.

**Next Action:** Initiate Day 1 tasks immediately.
