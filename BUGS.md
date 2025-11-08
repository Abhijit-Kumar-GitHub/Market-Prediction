# Bug Tracking & Issue Management

Someday soon i'll be setting this up on GitHub Issues
🟡 Acknowledged 
🟢 Resolved (v0.0.2) 

---

## 🐛 Active Bugs


### [BUG-001] Order book reconstruction memory leak
**Status:** 🟢 Resolved (v0.0.2)  
**Priority:** High  
**Reported:** 2025-10-28  
**Resolved:** 2025-10-28

**Description:**
Memory usage grows unbounded during long data collection runs

**Root Cause:**
Order book dictionary not clearing old price levels

**Solution:**
Added logic to remove price levels when quantity = 0


---

## ⚠️ Known Issues

### [ISSUE-001] WebSocket connection occasionally drops
**Status:** 🟢 Resolved (v0.0.2) 
**Priority:** Medium  
**Workaround:** Auto-restart script handles this

**Description:**
Coinbase WebSocket disconnects randomly every 6-12 hours

**Workaround:**
`run_collector_24x7.py` automatically restarts on disconnect

**Long-term Fix:**
Fixed it by ensuring thats restarts are not just for the crashed but websocket disconnects and normal closure of the script. it will keep on running until it fails consecutively for 8 times. 
---

## 📋 Technical Debt

### [DEBT-001] Hard-coded file paths
**Priority:** Medium  
**Effort:** 2 hours

**Description:**
File paths are hard-coded in multiple places. Should use config file.

**Affected Files:**
- `data_collector.py`
- `feature_engineer.py`

**Proposed Solution:**
Create `config.yaml`:
```yaml
data:
  raw_dir: "crypto_data_jsonl"
  processed_dir: "processed_data"
  
collection:
  buffer_size: 1000
  flush_interval: 30
```

---

### [DEBT-002] No unit tests
**Priority:** High  
**Effort:** 8 hours

**Description:**
Critical functions lack unit tests

**Needs Tests:**
- Feature engineering functions
- Order book reconstruction
- Data validation

---

## 🔮 Future Enhancements

### [FEATURE-001] Real-time prediction API
**Priority:** Low (post-MVP)  
**Effort:** 3 days

**Description:**
Flask/FastAPI endpoint for real-time predictions

**Requirements:**
- Load trained model
- Accept order book snapshot
- Return prediction + confidence

---

### [FEATURE-002] Multi-asset support
**Priority:** Medium  
**Effort:** 1 day

**Description:**
Support multiple cryptocurrencies instead of just BTC/ETH

**Changes Needed:**
- Configurable product list
- Separate features per asset
- Cross-asset correlation features

---

### [FEATURE-003] Taking realtime data and updating the models periodically automatically
**Priority:** Low (post MVP)  
**Effort:** 1 Week  

**Description:**
Allow realtime updation of model and correct identification of current trends for currect prediction  

**Changes Needed:**  
Still doing research regarding that

---

## 📊 Issue Statistics

| Category | Open  | In Progress | Resolved |
|----------|-------|-------------|----------|
| Bugs | 0     | 0 | 1        |
| Issues | 0     | 0 | 0        |
| Technical Debt | 2     | 0 | 0        |
| Features | 3     | 0 | 0        |
| **Total** | **5** | **0** | **1**    |

---

## 🏷️ Issue Template

When adding a new issue, use this template:

```markdown
### [TYPE-XXX] Short description
**Status:** 🔴 Open / 🟡 In Progress / 🟢 Resolved  
**Priority:** High / Medium / Low  
**Reported:** YYYY-MM-DD  
**Assigned to:** Name

**Description:**
What is the problem?

**Root Cause:** (for bugs)
Why does this happen?

**Solution:** (for bugs)
How to fix?

**Steps to Reproduce:** (for bugs)
1. Step 1
2. Step 2
3. See error

**Resolution Checklist:**
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

**Related Files:**
- file1.py
- file2.py
```

---

## 🔄 Workflow

1. **New Issue Discovered**
   - Add to this file using template
   - Assign priority
   - Add to project roadmap if impacts timeline

2. **Working on Issue**
   - Change status to 🟡 In Progress
   - Create branch: `fix/bug-001` or `feature/feature-001`
   - Commit with reference: "Fix BUG-001: pandas import"

3. **Issue Resolved**
   - Change status to 🟢 Resolved
   - Add to CHANGELOG.md
   - Close GitHub issue (when created)
   - Update version number if needed

---

## 🚀 Migration to GitHub Issues

Future Plans

1. **Create GitHub Issues from this file**
   - Each bug/issue becomes a GitHub issue
   - Use labels: `bug`, `enhancement`, `documentation`, `technical-debt`
   - Link to project board

2. **Set up issue templates**
   - `.github/ISSUE_TEMPLATE/bug_report.md`
   - `.github/ISSUE_TEMPLATE/feature_request.md`

3. **Migrate this file's content**
   - Keep this file for historical reference
   - Update with: "Active issues tracked on GitHub: [link]"

---

## 📝 Notes

- Keep this file updated weekly during active development
- Archive resolved issues after 30 days
- Reference issue IDs in commit messages
- Link issues to CHANGELOG entries

---

*Last Updated: 2025-11-06*
