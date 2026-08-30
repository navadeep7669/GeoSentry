/**
 * GeoSentry Offline Synchronization Engine
 * Provides offline caching, pending sync queue, and automatic background sync
 * for remote field hazard reports.
 */

const OFFLINE_STORAGE_KEY = 'geosentry_offline_reports';

class OfflineSyncManager {
  constructor() {
    this.isOnline = navigator.onLine;
    this.initEventListeners();
    this.checkPendingSyncCount();
  }

  initEventListeners() {
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.updateNetworkBadge();
      this.syncPendingReports();
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
      this.updateNetworkBadge();
    });
  }

  getPendingReports() {
    try {
      const data = localStorage.getItem(OFFLINE_STORAGE_KEY);
      return data ? JSON.parse(data) : [];
    } catch (e) {
      console.error('Error reading offline storage', e);
      return [];
    }
  }

  savePendingReports(reports) {
    try {
      localStorage.setItem(OFFLINE_STORAGE_KEY, JSON.stringify(reports));
      this.checkPendingSyncCount();
    } catch (e) {
      console.error('Error saving to offline storage', e);
    }
  }

  enqueueReport(reportData) {
    const reports = this.getPendingReports();
    const queuedItem = {
      id: 'local_' + Date.now(),
      timestamp: new Date().toISOString(),
      status: 'PENDING_SYNC',
      data: reportData,
    };
    reports.push(queuedItem);
    this.savePendingReports(reports);
    return queuedItem;
  }

  async syncPendingReports() {
    const reports = this.getPendingReports();
    if (reports.length === 0) return;

    console.log(`[OfflineSync] Syncing ${reports.length} pending report(s) to server...`);
    const remainingReports = [];

    for (const item of reports) {
      try {
        const formData = new FormData();
        formData.append('latitude', item.data.latitude);
        formData.append('longitude', item.data.longitude);
        if (item.data.elevation_m) formData.append('elevation_m', item.data.elevation_m);
        if (item.data.description) formData.append('description', item.data.description);

        const token = localStorage.getItem('geosentry_token');
        const headers = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const resp = await fetch('/reports', {
          method: 'POST',
          headers: headers,
          body: formData,
        });

        if (resp.ok) {
          console.log(`[OfflineSync] Report ${item.id} successfully synced!`);
        } else {
          remainingReports.push(item);
        }
      } catch (err) {
        console.warn(`[OfflineSync] Sync failed for report ${item.id}, retaining in queue:`, err);
        remainingReports.push(item);
      }
    }

    this.savePendingReports(remainingReports);
    this.updateNetworkBadge();

    if (remainingReports.length === 0) {
      const toast = document.getElementById('offline-sync-toast');
      if (toast) {
        toast.className = 'fixed bottom-4 right-4 z-50 bg-emerald-900/90 text-emerald-200 border border-emerald-700 px-4 py-2 rounded-xl shadow-xl text-xs font-semibold flex items-center gap-2 transition';
        toast.innerHTML = '<i class="fa-solid fa-cloud-arrow-up text-emerald-400"></i> All offline field reports successfully synced!';
        setTimeout(() => toast.classList.add('hidden'), 4000);
      }
    }
  }

  checkPendingSyncCount() {
    const count = this.getPendingReports().length;
    const badge = document.getElementById('pending-sync-badge');
    if (badge) {
      if (count > 0) {
        badge.innerText = `${count} Pending Sync`;
        badge.classList.remove('hidden');
      } else {
        badge.classList.add('hidden');
      }
    }
  }

  updateNetworkBadge() {
    const badge = document.getElementById('network-status-badge');
    if (!badge) return;

    if (this.isOnline) {
      badge.className = 'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800';
      badge.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Online Synced';
    } else {
      badge.className = 'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-950 text-amber-300 border border-amber-800';
      badge.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span> Offline Mode (Local Cache Active)';
    }
  }
}

window.offlineSync = new OfflineSyncManager();
