# Coda Button & Webhook Setup Guide

How to set up a button in your Coda table that triggers the cloud transcription service.

## 🎯 Overview

Instead of running a local Python script, users will now:
1. Click a **"Generate Insights"** button in Coda
2. Coda automation sends webhook to your Railway service
3. Cloud service processes transcription in the background
4. Results appear in Coda table automatically

## 📋 Prerequisites

- ✅ Webhook service deployed to Railway (see README.md)
- ✅ Webhook URL from Railway (e.g., `https://your-app.up.railway.app`)
- ✅ Coda table set up with required columns

## 🔘 Option 1: Button Column (Recommended)

### Step 1: Add Button Column

1. Open your "Automated transcriber for Juston notes" table
2. Click **"+ Add column"** (far right)
3. Choose column type: **"Button"**
4. Name it: **"Generate Insights"**

### Step 2: Configure Button Action

1. Click the button column header → **"Column options"**
2. Under "Button action", select **"Open URL"**
3. Set the URL to:
   ```
   https://your-app.up.railway.app/api/webhook/transcribe/
   ```
   Replace `your-app` with your actual Railway app name

4. **Important**: We'll use an automation to actually trigger the webhook (buttons can't directly POST data)

### Step 3: Create Webhook Automation

Since Coda buttons can only open URLs (GET requests), we need an automation to send the POST request:

1. Open **Automations** (⚙️ → Automations)
2. Click **"+ New automation"**
3. Configure:

**Name**: "Trigger Transcription Webhook"

**Trigger**: "When button pushed"
- Button column: "Generate Insights"

**Action**: "Push to webhook"
- Method: `POST`
- URL: `https://your-app.up.railway.app/api/webhook/transcribe/`
- Headers:
  ```json
  {
    "Content-Type": "application/json",
    "X-Webhook-Secret": "your-webhook-secret" (if configured)
  }
  ```
- Body:
  ```json
  {
    "row_id": "thisRow.id",
    "audio_url": "thisRow.[Audio File URL]"
  }
  ```

**Using Coda formulas in the body**:
```
Concatenate('{"row_id":"', thisRow.id, '","audio_url":"', thisRow.[Audio File URL], '"}')
```

4. Click **"Done"** and activate the automation

### Step 4: Update Status on Button Click (Optional)

Add another action to the automation to set Status to "Processing":

1. Edit the automation
2. Click **"+ Add action"**
3. Action: "Modify rows"
4. Row: "thisRow"
5. Column: "Status"
6. Value: "Processing"

## 🔘 Option 2: Formula Button (Alternative)

You can also use a formula-based button that directly calls a webhook using Coda Packs:

### Step 1: Create Formula Column

1. Add new column type: **"Formula"**
2. Name: "Generate Insights"
3. Formula:
   ```
   Button("Generate Insights",
     OpenWindow("https://your-app.up.railway.app/api/webhook/transcribe/?row_id=" & thisRow.id)
   )
   ```

**Note**: This uses GET instead of POST, so you'd need to modify your Django view to accept GET requests.

## 🔘 Option 3: Using Coda Pack (Advanced)

For more control, create a custom Coda Pack:

1. Go to https://coda.io/packs
2. Create new Pack
3. Add formula that POSTs to your webhook
4. Install Pack in your doc
5. Use in button column

Example Pack code (TypeScript):
```typescript
pack.addFormula({
  name: "TriggerTranscription",
  description: "Trigger audio transcription",
  parameters: [
    coda.makeParameter({
      type: coda.ParameterType.String,
      name: "rowId",
      description: "Row ID to process"
    }),
  ],
  resultType: coda.ValueType.String,
  execute: async function ([rowId], context) {
    const response = await context.fetcher.fetch({
      method: "POST",
      url: "https://your-app.up.railway.app/api/webhook/transcribe/",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        row_id: rowId
      }),
    });
    return "Queued!";
  },
});
```

## 📊 Complete Workflow Setup

### Required Columns

| Column Name | Type | Purpose |
|-------------|------|---------|
| Audio File URL | Text/Link | Google Drive shareable link |
| Generate Insights | Button | Triggers webhook |
| Status | Select | Processing status |
| Transcript | Text | Full transcript (auto-filled) |
| Summary | Text | Analysis summary (auto-filled) |
| Processed Date | Date/Time | Completion timestamp (auto-filled) |

### Status Values

Set up these options in the Status column:
- **Pending** - Default, waiting for button click
- **Processing** - Button clicked, task queued
- **Transcription Done** - Completed successfully
- **Failed** - Error occurred

### Recommended Automations

**Automation 1: Trigger Webhook on Button**
```
WHEN: Button "Generate Insights" is pushed
ACTION 1: Set Status to "Processing"
ACTION 2: Push to webhook
  URL: https://your-app.up.railway.app/api/webhook/transcribe/
  Body: {"row_id":"thisRow.id"}
```

**Automation 2: Mark Complete** (Same as before)
```
WHEN: Row is updated
IF: Transcript is not empty AND Status = "Processing"
THEN: Set Status to "Transcription Done"
```

**Automation 3: Notify on Completion** (Optional)
```
WHEN: Status changes to "Transcription Done"
ACTION: Send email or Slack notification
```

## 🧪 Testing the Setup

### Step 1: Test Health Endpoint

```bash
curl https://your-app.up.railway.app/api/health/
```

Expected response:
```json
{
  "status": "healthy",
  "service": "transcription-webhook",
  "version": "1.0.0"
}
```

### Step 2: Test Webhook with curl

```bash
curl -X POST https://your-app.up.railway.app/api/webhook/transcribe/ \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your-secret" \
  -d '{
    "row_id": "i-OQq0AURiBG",
    "audio_url": "https://drive.google.com/file/d/..."
  }'
```

Expected response:
```json
{
  "status": "queued",
  "task_id": "abc-123-def-456",
  "row_id": "i-OQq0AURiBG",
  "message": "Transcription task has been queued"
}
```

### Step 3: Test in Coda

1. Add a row with:
   - Audio File URL: Google Drive link
   - Status: "Pending"
2. Click "Generate Insights" button
3. Status should change to "Processing"
4. Wait ~30-60 seconds
5. Check if Transcript and Summary are filled
6. Status should change to "Transcription Done"

## 🎨 UI Enhancements

### Color-Code Status

1. Click Status column → Options → Conditional formatting
2. Set colors:
   - Processing = Yellow 🟡
   - Transcription Done = Green 🟢
   - Failed = Red 🔴

### Hide Button After Processing

Add condition to button column:
```
If(thisRow.Status = "Pending",
   Button("Generate Insights"),
   "✓ Processed"
)
```

### Show Processing Indicator

Add a formula column:
```
Switch(thisRow.Status,
  "Pending", "⏸️ Ready",
  "Processing", "⏳ Processing...",
  "Transcription Done", "✅ Complete",
  "Failed", "❌ Error",
  "❓ Unknown"
)
```

## 🔧 Troubleshooting

### Button Does Nothing

**Check**:
- Automation is active
- Webhook URL is correct
- Railway service is running

**Debug**:
- Check Railway logs
- Look for webhook requests
- Verify JSON body format

### Status Stuck on "Processing"

**Possible causes**:
- Task failed silently
- Celery worker not running
- Redis connection issue

**Fix**:
- Check Railway worker service logs
- Verify Redis service is running
- Check task status endpoint:
  ```
  GET https://your-app.up.railway.app/api/status/{task_id}/
  ```

### Webhook Returns Error

**Check Railway logs**:
- Web service logs for incoming requests
- Worker logs for task processing

**Common errors**:
- Invalid row_id
- Missing audio_url
- Google Drive download failed
- Whisper model out of memory

## 📈 Usage Example

### Typical Workflow

1. **User**: Uploads audio to Google Drive, shares link
2. **User**: Pastes link in Coda table row
3. **User**: Clicks "Generate Insights" button
4. **Automation**: Sets Status to "Processing", sends webhook
5. **Railway Service**: Receives webhook, queues task
6. **Celery Worker**: Downloads audio, transcribes, analyzes
7. **Service**: Updates Coda row with results
8. **Automation**: Changes Status to "Transcription Done"
9. **User**: Sees completed transcript and summary!

### Batch Processing

To process multiple rows:
1. Add all audio URLs
2. Click "Generate Insights" on each row
3. All tasks queue in parallel
4. Results appear as each completes

## 🚀 Advanced Features

### Rate Limiting

Add delay between webhook calls in Coda automation:
- Settings → Add delay of 10 seconds between rows

### Retry Failed Tasks

Add button for retry:
```
If(thisRow.Status = "Failed",
   Button("Retry",
     ModifyRows(thisRow, Status, "Pending")
   ),
   ""
)
```

### Track Processing Time

Add formula column:
```
If(thisRow.[Processed Date].IsNotBlank(),
   thisRow.[Processed Date] - thisRow.[Button Clicked Date],
   "Processing..."
)
```

## ✅ Checklist

Before going live:

- [ ] Railway service deployed and healthy
- [ ] Redis service running
- [ ] Celery worker deployed
- [ ] Environment variables configured
- [ ] Health endpoint responding
- [ ] Webhook endpoint tested with curl
- [ ] Button column added to Coda table
- [ ] Webhook automation created and active
- [ ] Status automation set up
- [ ] Test row processed successfully
- [ ] Webhook secret configured (optional but recommended)
- [ ] Monitoring/alerts set up

---

**Ready to use!** Click the button and watch the magic happen! ✨
