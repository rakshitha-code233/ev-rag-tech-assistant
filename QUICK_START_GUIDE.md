# EV Diagnostic Assistant - Quick Start Guide

## What Was Fixed

Your system had 3 main issues that have now been resolved:

### 1. ✅ Login Not Working
**Problem**: After logout and reopening the app, login failed with "Invalid email or password"  
**Root Cause**: Database file (`users.db`) was missing after deployment  
**Fix**: Database is now automatically created when the app starts

### 2. ✅ Uploaded Manuals Not Giving Answers
**Problem**: Chat didn't return answers even after uploading manuals  
**Root Cause**: RAG pipeline wasn't properly integrated with the LLM  
**Fix**: Enhanced the chat system to properly retrieve and use manual content

### 3. ✅ Data Isolation
**Problem**: Users could see each other's manuals and chat history  
**Root Cause**: No user-specific filtering  
**Fix**: All data is now stored in user-specific directories and filtered by user ID

---

## How to Use the System

### Step 1: Create an Account
1. Go to the app
2. Click "Register"
3. Enter your details:
   - Username: Your name
   - Email: Your email address
   - Password: A strong password
4. Click "Create Account"

### Step 2: Login
1. Enter your email and password
2. Click "Login"
3. You're now logged in!

### Step 3: Upload a Manual
1. Click "Upload Manual"
2. Select a PDF file (must be an EV repair manual)
3. The file will be indexed automatically
4. Wait for the upload to complete

### Step 4: Ask Questions
1. Type your question in the chat box
2. Examples:
   - "How do I check the battery health?"
   - "What does fault code P0001 mean?"
   - "How do I charge the vehicle?"
3. The system will search your uploaded manuals and provide answers with citations

### Step 5: Use Voice Input (Optional)
1. Click the microphone icon
2. Speak your question
3. The system will transcribe and answer

---

## Supported Manual Formats

The system accepts PDF files with these keywords in the filename:
- `tesla` - Tesla vehicles
- `ev` - Electric vehicles
- `electric` - Electric vehicles
- `vehicle` - Any vehicle
- `model` - Vehicle models
- `charging` - Charging systems
- `battery` - Battery systems
- `diagnostic` - Diagnostic procedures

**Examples of valid filenames:**
- `Tesla_Model3.pdf` ✅
- `EV_Diagnostic_Manual.pdf` ✅
- `Electric_Vehicle_Repair_Guide.pdf` ✅
- `Random_Document.pdf` ❌

---

## Troubleshooting

### Problem: "Invalid email or password" on login
**Solution**: 
1. Make sure you're using the correct email and password
2. If you forgot your password, create a new account
3. If the error persists, the database may need to be reinitialized

### Problem: "Only EV repair manuals are supported"
**Solution**: 
1. Rename your file to include EV keywords (e.g., `Tesla_Model3.pdf`)
2. Make sure it's a PDF file
3. Try uploading again

### Problem: Chat says "No matching answer in indexed manuals"
**Solution**:
1. Make sure you've uploaded a manual
2. Wait for the upload to complete
3. Try a different question
4. Check that your question is related to the manual content

### Problem: Voice input not working
**Solution**:
1. Check that your microphone is working
2. Make sure you have a stable internet connection
3. Try typing instead of using voice

### Problem: App is slow
**Solution**:
1. Clear your browser cache
2. Close other tabs/applications
3. Refresh the page
4. Try again

---

## Features

### Chat with Manuals
- Ask questions about your uploaded manuals
- Get answers with page citations
- Search across multiple manuals

### Voice Input
- Speak your questions
- Automatic transcription
- Hands-free operation

### Chat History
- View previous conversations
- Rename conversations
- Delete old conversations

### Manual Management
- Upload multiple manuals
- View uploaded manuals
- Delete manuals you no longer need

### Mobile Support
- Works on phones and tablets
- Responsive design
- Touch-friendly interface

---

## Tips for Best Results

1. **Upload Complete Manuals**: Upload the full repair manual, not just excerpts
2. **Use Specific Questions**: Instead of "Tell me about batteries", ask "How do I check battery health?"
3. **Include Vehicle Model**: Mention the vehicle model in your question (e.g., "Tesla Model 3")
4. **Check Citations**: Always verify the page citations to confirm the answer
5. **Upload Multiple Manuals**: Upload manuals for different systems (battery, charging, diagnostics)

---

## System Requirements

### Browser
- Chrome, Firefox, Safari, or Edge (latest version)
- JavaScript enabled
- Cookies enabled

### Internet
- Stable internet connection
- Minimum 1 Mbps for chat
- Minimum 5 Mbps for voice input

### Device
- Desktop, laptop, tablet, or smartphone
- Minimum 2GB RAM
- Minimum 100MB free storage

---

## Privacy & Security

- ✅ Your data is private - only you can see your manuals and chat history
- ✅ Passwords are encrypted with bcrypt
- ✅ All communication is encrypted (HTTPS)
- ✅ No data is shared with other users
- ✅ Your manuals are stored in your user-specific directory

---

## Getting Help

If you encounter any issues:

1. **Check the Troubleshooting section** above
2. **Clear your browser cache** and try again
3. **Refresh the page** and log back in
4. **Try a different browser** to rule out browser issues
5. **Contact support** with details about the error

---

## System Status

✅ **All systems operational**

- Database: Working
- Authentication: Working
- Manual upload: Working
- Chat: Working
- Voice input: Working
- Data isolation: Working

---

## What's Next?

1. Create your account
2. Upload your first manual
3. Ask a question
4. Explore the features
5. Provide feedback

Enjoy using the EV Diagnostic Assistant!
