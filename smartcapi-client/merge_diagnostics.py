"""
Script to merge UserDiagnostics functionality into RekapitulasiUser.vue
"""
import re

# Read the original RekapitulasiUser.vue
with open(r'c:\xampp\htdocs\smartcapi_pwa\smartcapi-client\src\pages\RekapitulasiUser.vue', 'r', encoding='utf-8') as f:
    rekap_content = f.read()

# Read UserDiagnostics.vue to extract the diagnostics modal template
with open(r'c:\xampp\htdocs\smartcapi_pwa\smartcapi-client\src\pages\UserDiagnostics.vue', 'r', encoding='utf-8') as f:
    diag_content = f.read()

# Extract the diagnostics template (lines 1-302 from UserDiagnostics)
diag_template_match = re.search(r'(<div class="diagnostics-page">.*?</div>\s*</template>)', diag_content, re.DOTALL)
if diag_template_match:
    diag_template = diag_template_match.group(1)
    # Convert to modal format
    diag_modal = f'''
    <!-- Diagnostics Modal -->
    <div v-if="showDiagnosticsModal" class="modal-overlay diagnostics-overlay" @click.self="closeDiagnostics">
      {diag_template.replace('class="diagnostics-page"', 'class="diagnostics-modal"')}
    </div>'''
else:
    print("Could not extract diagnostics template")
    diag_modal = ""

# Find where to insert the Detail button (in the Action column)
action_col_pattern = r'(<td data-label="Action" class="action-col">)(.*?)(</td>)'
action_col_match = re.search(action_col_pattern, rekap_content, re.DOTALL)

if action_col_match:
    original_actions = action_col_match.group(2)
    # Add Detail button at the beginning
    new_actions = f'''
              <button class="action-btn detail-btn" @click="openDiagnostics(row)" title="View Diagnostics">Detail</button>{original_actions}'''
    
    rekap_content = rekap_content.replace(action_col_match.group(0), 
                                          f'{action_col_match.group(1)}{new_actions}{action_col_match.group(3)}')

# Find where to insert the diagnostics modal (before </div> at the end of template)
template_end_pattern = r'(</div>\s*</template>)'
template_end_match = re.search(template_end_pattern, rekap_content)

if template_end_match:
    insert_pos = template_end_match.start()
    rekap_content = rekap_content[:insert_pos] + diag_modal + '\n  ' + rekap_content[insert_pos:]

# Add diagnostics state and functions to script
script_pattern = r'(<script setup>.*?)(</script>)'
script_match = re.search(script_pattern, rekap_content, re.DOTALL)

if script_match:
    script_content = script_match.group(1)
    
    # Add diagnostics state variables
    diagnostics_state = '''
// Diagnostics Modal State
const showDiagnosticsModal = ref(false);
const diagnosticsData = ref(null);
const diagnosticsLoading = ref(false);
const diagnosticsError = ref('');

const hasInterviewAudio = computed(() => {
  if (!diagnosticsData.value) return false;
  return diagnosticsData.value.interviews.some(i => i.raw_audio_path);
});

const interviewsWithAudio = computed(() => {
  if (!diagnosticsData.value) return [];
  return diagnosticsData.value.interviews.filter(i => i.raw_audio_path);
});

const hasAudioChunks = computed(() => {
  if (!diagnosticsData.value) return false;
  return diagnosticsData.value.interviews.some(i => i.audio_chunks && i.audio_chunks.length > 0);
});

const hasRespondentData = computed(() => {
  if (!diagnosticsData.value) return false;
  return diagnosticsData.value.interviews.some(i => i.respondent);
});

'''
    
    # Add diagnostics functions
    diagnostics_functions = '''
async function openDiagnostics(row) {
  showDiagnosticsModal.value = true;
  diagnosticsLoading.value = true;
  diagnosticsError.value = '';
  diagnosticsData.value = null;
  
  try {
    const token = authStore.userToken.value;
    const response = await api.getUserDiagnostics(row.username, token);
    diagnosticsData.value = response.data;
  } catch (err) {
    console.error('Error loading diagnostics:', err);
    diagnosticsError.value = err.response?.data?.detail || 'Gagal memuat data diagnostik';
  } finally {
    diagnosticsLoading.value = false;
  }
}

function closeDiagnostics() {
  showDiagnosticsModal.value = false;
  diagnosticsData.value = null;
  diagnosticsError.value = '';
}

function formatDate(dateString) {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return date.toLocaleString('id-ID');
}

async function extractMFCC() {
  if (!diagnosticsData.value) return;
  
  if (confirm('Ekstrak MFCC features dari voice sample registrasi?')) {
    try {
      diagnosticsLoading.value = true;
      const token = authStore.userToken.value;
      await api.extractUserMFCC(diagnosticsData.value.id, token);
      alert('MFCC extraction berhasil!');
      // Reload diagnostics data
      const response = await api.getUserDiagnostics(diagnosticsData.value.username, token);
      diagnosticsData.value = response.data;
    } catch (err) {
      console.error('Error extracting MFCC:', err);
      alert('Gagal ekstrak MFCC: ' + (err.response?.data?.detail || err.message));
    } finally {
      diagnosticsLoading.value = false;
    }
  }
}

'''
    
    # Insert before the last function (logout)
    logout_pattern = r'(function logout\(\) {)'
    if re.search(logout_pattern, script_content):
        script_content = re.sub(logout_pattern, diagnostics_state + diagnostics_functions + r'\1', script_content)
    
    rekap_content = rekap_content.replace(script_match.group(0), script_content + '</script>')

# Add diagnostics modal styles
style_pattern = r'(</style>)'
style_match = re.search(style_pattern, rekap_content)

if style_match:
    diagnostics_styles = '''
/* Diagnostics Modal Styles */
.diagnostics-overlay {
  overflow-y: auto;
  padding: 20px;
}

.diagnostics-modal {
  background: #f5f7fa;
  border-radius: 16px;
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px;
  max-height: 90vh;
  overflow-y: auto;
}

.detail-btn {
  background-color: #667eea;
  color: white;
}

.detail-btn:hover {
  background-color: #5568d3;
}

'''
    rekap_content = rekap_content.replace(style_match.group(0), diagnostics_styles + style_match.group(0))

# Write the merged content
with open(r'c:\xampp\htdocs\smartcapi_pwa\smartcapi-client\src\pages\RekapitulasiUser.vue', 'w', encoding='utf-8') as f:
    f.write(rekap_content)

print("Successfully merged UserDiagnostics into RekapitulasiUser.vue")
