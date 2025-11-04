# Documentation Quick Reference Card

Keep this handy while working on your project!

---

## 📋 Daily Workflow

### Every Coding Session
```
1. [ ] Check BUGS.md for active issues
2. [ ] Code and test changes
3. [ ] Add/update code comments
4. [ ] Git commit with clear message
5. [ ] Update BUGS.md if issues found
```

### Git Commit Message Format
```bash
# Pattern: type: description [version] [issue-id]

git commit -m "feat: Add K-Means clustering [v0.4.0]"
git commit -m "fix: Handle NaN in features [v0.3.1] [BUG-003]"
git commit -m "docs: Update README with results"
git commit -m "refactor: Optimize memory usage"
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

---

## 🔄 When to Update Each File

| File | Update When | Example |
|------|-------------|---------|
| **README.md** | Phase complete, results ready | "Updated model comparison table" |
| **CHANGELOG.md** | Every version bump | "Released v0.4.0" |
| **BUGS.md** | Bug found or fixed | "Added BUG-004: memory leak" |
| **PROJECT_ROADMAP.md** | Weekly progress check | "Checked off Week 4 tasks" |
| **requirements.txt** | New package installed | "Added scikit-learn==1.0.0" |
| **Technical Report** | End of each phase | "Completed results section" |

---

## 📦 Version Bumping Guide

### When to Bump MINOR (0.X.0)
✅ Completed a major phase (data collection, feature engineering, etc.)  
✅ Added significant new functionality  
✅ Reached a milestone in PROJECT_ROADMAP.md

### When to Bump PATCH (0.0.X)
✅ Fixed a bug  
✅ Performance optimization  
✅ Code refactoring (no new features)  
✅ Documentation-only updates

### How to Bump
```bash
# 1. Update CHANGELOG.md
# Add new version section with changes

# 2. Commit
git add .
git commit -m "Release v0.4.0: Unsupervised learning complete"

# 3. Tag
git tag -a v0.4.0 -m "Release v0.4.0"

# 4. Push
git push origin main
git push origin v0.4.0
```

---

## 🐛 Bug Tracking Workflow

### New Bug Found
```markdown
1. Open BUGS.md
2. Add to "Active Bugs" section:

### [BUG-XXX] Short description
**Status:** 🔴 Open
**Priority:** High/Medium/Low
**Reported:** YYYY-MM-DD

**Description:** What's wrong?
**Root Cause:** Why does it happen?
**Solution:** How to fix?

**Resolution:**
- [ ] Fix implemented
- [ ] Tests added
- [ ] Docs updated
```

### Bug Fixed
```markdown
1. Update status: 🟢 Resolved (vX.X.X)
2. Add to CHANGELOG.md under "Fixed"
3. Commit: "fix: Description [vX.X.X] [BUG-XXX]"
```

---

## 📝 README.md Update Stages

### Stage 1: Development (Keep Placeholders)
```markdown
## Results (In Progress)
- Data: ✅ 14 days collected
- Models: 🟡 Training K-Means
- Accuracy: TBD
```

### Stage 2: Results Ready (Add Numbers)
```markdown
## Results
| Model | Accuracy |
|-------|----------|
| SVM | 68.3% |
| RF | 71.2% |
```

### Stage 3: Final (Add Context)
```markdown
## Key Findings
✅ Order book imbalance is strongest predictor (importance: 0.32)
✅ Regime-aware models improve accuracy by 18%
```

---

## ⚡ Quick Commands

### Check Status
```powershell
# What files changed?
git status

# What changed in README?
git diff README.md

# Recent commits
git log --oneline -5
```

### Update Dependencies
```powershell
# Install new package
pip install pandas

# Update requirements.txt
pip freeze > requirements.txt
```

### Find TODOs
```powershell
# In PowerShell
Select-String -Path *.md -Pattern "TODO|FIXME|XXX|TBD"
```

---

## 📊 Weekly Checklist

**Every Friday (or end of week):**

- [ ] Review BUGS.md - any new issues?
- [ ] Update PROJECT_ROADMAP.md - check off completed tasks
- [ ] Update CHANGELOG.md if version changed
- [ ] Review README.md - is status current?
- [ ] Git commit all documentation changes
- [ ] Backup data files (if collecting)

---

## 🎯 Before Each Phase Complete

**Checklist before bumping version:**

- [ ] All code for this phase working
- [ ] Tests pass (if you have tests)
- [ ] CHANGELOG.md updated with changes
- [ ] README.md updated with new features/results
- [ ] Project roadmap checkboxes marked
- [ ] Git commit with version number
- [ ] Git tag created
- [ ] Technical report section updated (if applicable)

---

## 🚨 Emergency: Something Broke!

### Quick Fix Process
```
1. Don't panic!
2. Open BUGS.md
3. Document the issue (what, when, why)
4. Try to isolate the problem
5. Check git log for recent changes
6. Revert if needed: git revert <commit-hash>
7. Fix properly, then:
   - Update BUGS.md status
   - Commit: "fix: [BUG-XXX] description"
   - Bump PATCH version if significant
```

---

## 📧 Pre-Share Checklist

**Before making repository public:**

- [ ] README has no placeholders (XX%, TBD)
- [ ] All metrics are actual numbers
- [ ] CHANGELOG is complete
- [ ] BUGS.md has no embarrassing entries
- [ ] requirements.txt is current
- [ ] Code has no TODOs in critical places
- [ ] Spelling/grammar checked
- [ ] Links tested
- [ ] Fresh clone works
- [ ] Screenshots/plots are current

---

## 🎨 Documentation Style Guide

### Status Emojis
- 🔴 Not started / Open
- 🟡 In progress / Acknowledged
- 🟢 Complete / Resolved
- ✅ Done / Checked
- ❌ Failed / Error
- ⚠️ Warning / Caution

### Formatting
```markdown
# Use consistent formatting

**Bold** for emphasis
`code` for filenames/commands
> Quote for important notes

## Tables for comparisons
| Column | Value |
|--------|-------|
| Item | 123 |

- Bullet points for lists
1. Numbered for steps
```

---

## 📚 Documentation Files at a Glance

| File | Purpose | Update Frequency |
|------|---------|------------------|
| README.md | Project homepage | Weekly |
| CHANGELOG.md | Version history | Each release |
| BUGS.md | Issue tracking | When found/fixed |
| PROJECT_ROADMAP.md | Timeline & progress | Weekly |
| requirements.txt | Dependencies | When changed |
| Technical Report | Academic writeup | Each phase |
| Presentation | Slides for demo | After results |
| CV Descriptions | Resume text | Final polish |

---

## 🎓 Common Scenarios

### "I just fixed a bug"
```
1. Update BUGS.md (change status to Resolved)
2. Update CHANGELOG.md (add to "Fixed" section)
3. Commit: "fix: Description [v0.X.Y] [BUG-XXX]"
4. Bump PATCH version if significant
```

### "I completed a major phase"
```
1. Update README.md (add results)
2. Update CHANGELOG.md (new version section)
3. Update PROJECT_ROADMAP.md (check off phase)
4. Bump MINOR version
5. Create git tag
6. Update technical report section
```

### "I added a new feature"
```
1. Document in code (docstrings)
2. Update README.md (feature list)
3. Update CHANGELOG.md ("Added" section)
4. Commit: "feat: Description"
5. Consider bumping MINOR if significant
```

### "I'm sharing my project"
```
1. Go through pre-share checklist
2. Update all placeholders
3. Final README polish
4. Make repo public
5. Update CV/LinkedIn
6. Share with network
```

---

## 💡 Pro Tips

✅ **Document as you code** - Don't leave it for later  
✅ **Commit often** - Small, logical commits with clear messages  
✅ **Update weekly** - Set a recurring reminder  
✅ **Use templates** - Consistency is professional  
✅ **Test links** - Broken links look unprofessional  
✅ **Spell check** - Grammarly is your friend  
✅ **Get feedback** - Have someone review your README  

---

## 🔗 Quick Links

- [CHANGELOG format](https://keepachangelog.com/)
- [Semantic Versioning](https://semver.org/)
- [Good README examples](https://github.com/matiassingers/awesome-readme)
- [Commit message conventions](https://www.conventionalcommits.org/)

---

**Print this page and keep it visible while coding!**

*Last Updated: 2025-11-02*
