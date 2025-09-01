# Security Guidelines - WindVoice-Windows

## 🔒 Credential Management

### ⚠️ NEVER commit credentials to the repository

- **API Keys** - Never include real API keys in code or config files
- **URLs** - Don't hardcode internal Thomson Reuters URLs
- **Personal Info** - Keep email addresses and user identifiers private

### ✅ Secure Configuration

WindVoice stores all sensitive credentials in:
```
~/.windvoice/config.toml
```

This file is:
- ✅ Created locally on each user's machine
- ✅ Never committed to git (excluded by .gitignore)
- ✅ Only readable by the user account

### 🛡️ Best Practices

1. **Use the setup script**: `python setup_config.py`
2. **Keep credentials private**: Never share your API keys
3. **Use examples safely**: `config.example.toml` has empty placeholders
4. **Regular rotation**: Update API keys periodically

### 📝 Configuration Template

```toml
[litellm]
api_key = ""           # Your virtual API key (sk-xxxxx)
api_base = ""          # Thomson Reuters proxy URL
key_alias = ""         # Your email identifier
model = "whisper-1"
```

## 🚨 If You Accidentally Commit Credentials

1. **Immediate action**: Contact Thomson Reuters admin to rotate keys
2. **Git cleanup**: Use `git filter-branch` or BFG Repo-Cleaner
3. **Update .gitignore**: Ensure files are properly excluded
4. **Re-encrypt**: Generate new credentials

## 📞 Support

For credential issues, contact your Thomson Reuters administrator.