import os

file_path = r"c:\xampp\htdocs\smartcapi_pwa\smartcapi-client\src\pages\Database.vue"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replacement 1: Add recording check
target_1 = "async function exportInterviewMfcc(row) {\n  try {"
replacement_1 = """async function exportInterviewMfcc(row) {
  if (!row.has_recording && !row.recording_path) {
    alert("Interview ini tidak memiliki rekaman audio.");
    return;
  }

  try {"""

if target_1 in content:
    content = content.replace(target_1, replacement_1)
    print("Applied replacement 1")
else:
    print("Target 1 not found")
    # Try with different whitespace if needed, but let's see

# Replacement 2: Improve error handling
target_2 = """  } catch (error) {
    console.error('Failed to export MFCC:', error);
    alert('Gagal mengekspor MFCC: ' + (error.response?.data?.detail || error.message));
  }
}"""
replacement_2 = """  } catch (error) {
    console.error('Failed to export MFCC:', error);
    
    let errorMessage = 'Gagal mengekspor MFCC';
    
    if (error.response && error.response.data instanceof Blob) {
        try {
            const text = await error.response.data.text();
            const data = JSON.parse(text);
            if (data.detail) errorMessage += ': ' + data.detail;
        } catch (e) {
            errorMessage += ': ' + (error.response.statusText || error.message);
        }
    } else if (error.response?.data?.detail) {
        errorMessage += ': ' + error.response.data.detail;
    } else {
        errorMessage += ': ' + error.message;
    }

    alert(errorMessage);
  }
}"""

if target_2 in content:
    content = content.replace(target_2, replacement_2)
    print("Applied replacement 2")
else:
    print("Target 2 not found")

# Replacement 3: Add CSS
target_3 = """.intv-mfcc-btn:hover {
  background-color: #138496;
}"""
replacement_3 = """.intv-mfcc-btn:hover {
  background-color: #138496;
}

.action-btn:disabled,
.action-btn.disabled {
  background-color: #ccc;
  cursor: not-allowed;
  opacity: 0.7;
}

.action-btn:disabled:hover,
.action-btn.disabled:hover {
  background-color: #ccc;
  transform: none;
}"""

if target_3 in content:
    content = content.replace(target_3, replacement_3)
    print("Applied replacement 3")
else:
    print("Target 3 not found")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
