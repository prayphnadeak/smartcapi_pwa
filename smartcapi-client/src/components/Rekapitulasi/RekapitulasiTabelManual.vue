<template>
  <div class="table-container">
    <table class="recap-table">
      <thead>
        <tr>
          <th class="no-column">No</th>
          <th class="name-column">Nama Responden</th>
          <th class="status-column">Status Pendataan</th>
          <th class="duration-column">Durasi Wawancara (detik)</th>
          <th class="date-column">Tanggal Wawancara</th>
          <th class="action-column">Action</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="data.length === 0">
          <td colspan="5" class="empty-state">Belum ada data untuk ditampilkan.</td>
        </tr>
        <tr v-for="(item, index) in data" :key="item.id">
          <td class="no-column" data-label="No">{{ index + 1 }}</td>
          <td class="name-column" data-label="Nama Responden">{{ item.respondent_name }}</td>
          <td class="status-column" data-label="Status Pendataan">
            <span :class="getStatusClass(item.status)">
              {{ formatStatus(item.status) }}
            </span>
          </td>
          <td class="duration-column" data-label="Durasi Wawancara">{{ item.duration || 0 }}</td>
          <td class="date-column" data-label="Tanggal Wawancara">{{ formatDate(item.created_at) }}</td>
          <td class="action-column" data-label="Action">
            <button class="icon-btn edit-btn" title="Edit Data" @click="handleEdit(item)">
              ✏️
            </button>
            <button class="icon-btn delete-btn" title="Hapus Data" @click="handleDelete(item)">
              🗑️
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
defineProps({
  data: { type: Array, required: true },
  getStatusClass: { type: Function, required: true },
  formatStatus: { type: Function, required: true },
  handleEdit: { type: Function, required: true },
  handleDelete: { type: Function, required: true },
});

// Helper to format date
function formatDate(dateString) {
  if (!dateString) return '-';
  const date = new Date(dateString);
  const day = String(date.getDate()).padStart(2, '0');
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const year = date.getFullYear();
  return `${day}/${month}/${year}`;
}
</script>

<style scoped>
.table-container { padding-top: 20px; overflow-x: auto; }
.recap-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.recap-table th { background: #f0f0f0; color: #333; padding: 12px 8px; text-align: center; font-weight: 600; border-bottom: 2px solid #ddd; }
.recap-table td { padding: 10px 8px; border-bottom: 1px solid #ddd; text-align: center; vertical-align: middle; }
.no-column { width: 50px; }
.name-column { text-align: left; min-width: 200px; }
.status-column { width: 120px; }
.duration-column { width: 150px; font-weight: 500; }
.date-column { width: 150px; }
.empty-state { padding: 40px; text-align: center; color: #888; }

.status-badge { padding: 4px 12px; border-radius: 15px; font-size: 12px; font-weight: 600; }
.status-submitted { background: #d4edda; color: #155724; }
.status-pending { background: #fff3cd; color: #856404; }
.status-no-data { background: #f8d7da; color: #721c24; }

/* Style untuk kolom dan tombol Action */
.action-column { width: 100px; }
.icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 18px;
  padding: 5px;
  margin: 0 5px;
  border-radius: 50%;
  transition: background-color 0.2s;
}
.icon-btn:hover { background-color: #f0f0f0; }
.edit-btn:hover { background-color: #d4edda; }
.delete-btn:hover { background-color: #f8d7da; }

/* Responsive Styles for Mobile */
@media screen and (max-width: 768px) {
  .recap-table thead {
    display: none;
  }
  .recap-table tbody, .recap-table tr, .recap-table td {
    display: block;
    width: 100%;
  }
  .recap-table tr {
    margin-bottom: 1rem;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  }
  .recap-table td {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 15px;
    border-bottom: 1px solid #f0f0f0;
    text-align: right;
    white-space: normal;
  }
  .recap-table td::before {
    content: attr(data-label);
    font-weight: 600;
    color: #333;
    text-align: left;
    padding-right: 1rem;
    flex: 1;
  }
  .recap-table td:last-child {
    border-bottom: none;
  }
  .no-column, .name-column, .status-column, .duration-column, .date-column, .action-column {
    width: auto;
    text-align: right;
  }
  .action-column {
    justify-content: flex-end;
    gap: 8px;
  }
}
</style>