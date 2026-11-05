document.addEventListener('DOMContentLoaded', () => {
  const body = document.body;
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'dark') {
    body.classList.add('dark');
  }

  const themeButton = document.querySelector('[data-theme-toggle]');
  if (themeButton) {
    const setIcon = () => {
      const icon = themeButton.querySelector('i');
      if (!icon) return;
      if (body.classList.contains('dark')) {
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
      } else {
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
      }
    };

    setIcon();
    themeButton.addEventListener('click', () => {
      body.classList.toggle('dark');
      localStorage.setItem('theme', body.classList.contains('dark') ? 'dark' : 'light');
      setIcon();
    });
  }

  const menuToggle = document.querySelector('.menu-toggle');
  const sidebar = document.querySelector('.sidebar');
  if (menuToggle && sidebar) {
    menuToggle.addEventListener('click', () => {
      sidebar.classList.toggle('sidebar-hidden');
    });
  }

  initGlobalSearch();
  initCurrentLocation();
  initNotifications();
  initDashboard();
  initWeather();
  initMap();
  initFloodPrediction();
  initModulePrediction();
  initModuleAnalytics();
  initReportExport();
});

function initGlobalSearch() {
  const search = document.getElementById('global-search');
  const results = document.getElementById('search-results');
  if (!search || !results) return;

  const collectTargets = () => {
    const targets = [];
    document.querySelectorAll('.nav-item').forEach((node) => {
      targets.push({ label: node.textContent.trim(), detail: 'Page', href: node.getAttribute('href') });
    });
    document.querySelectorAll('.page-header h2, .panel-head h3, .stat-label, .category-card h4, .feature-card h3, .location-item h4, .alert-item h4').forEach((node) => {
      const target = node.closest('.panel-card, .stat-card, .category-card, .feature-card, section') || node;
      targets.push({ label: node.textContent.trim(), detail: 'This page', target });
    });
    return targets.filter((item) => item.label);
  };

  const hideResults = () => {
    results.hidden = true;
    results.replaceChildren();
  };

  search.addEventListener('input', () => {
    const query = search.value.trim().toLocaleLowerCase();
    results.replaceChildren();
    if (!query) {
      hideResults();
      return;
    }

    const matches = collectTargets()
      .filter((item) => item.label.toLocaleLowerCase().includes(query))
      .slice(0, 8);

    if (matches.length === 0) {
      const empty = document.createElement('div');
      empty.className = 'search-empty';
      empty.textContent = 'No matching pages or items found.';
      results.append(empty);
    } else {
      matches.forEach((item) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'search-result';
        button.setAttribute('role', 'option');
        const label = document.createElement('span');
        label.textContent = item.label;
        const detail = document.createElement('small');
        detail.textContent = item.detail;
        button.append(label, detail);
        button.addEventListener('click', () => {
          if (item.href) {
            window.location.assign(item.href);
          } else if (item.target) {
            item.target.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }
          hideResults();
        });
        results.append(button);
      });
    }
    results.hidden = false;
  });

  search.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') hideResults();
    if (event.key === 'Enter') results.querySelector('.search-result')?.click();
  });
  document.addEventListener('click', (event) => {
    if (!event.target.closest('.search-box')) hideResults();
  });
}

function initCurrentLocation() {
  const button = document.getElementById('current-location');
  const label = document.getElementById('current-location-label');
  if (!button || !label) return;

  const storedName = localStorage.getItem('locationName');
  if (storedName) label.textContent = storedName;
  const storedLatitude = localStorage.getItem('locationLatitude');
  const storedLongitude = localStorage.getItem('locationLongitude');
  if (storedLatitude && storedLongitude && /^-?\d+(\.\d+)?,\s*-?\d+(\.\d+)?$/.test(storedName || '')) {
    resolveLocationName(storedLatitude, storedLongitude).then((name) => {
      saveLocation(Number(storedLatitude), Number(storedLongitude), name);
    });
  }
  window.addEventListener('disasterguard:location-changed', (event) => {
    const dashboardLocation = document.getElementById('dashboard-weather-location');
    if (dashboardLocation) dashboardLocation.textContent = event.detail.name;
    if (document.getElementById('dashboard-page')) loadDashboardWeather();
  });

  button.addEventListener('click', () => {
    if (!navigator.geolocation) {
      button.title = 'Location services are not supported by this browser.';
      return;
    }

    button.disabled = true;
    label.textContent = 'Finding location...';
    navigator.geolocation.getCurrentPosition(async (position) => {
      const { latitude, longitude } = position.coords;
      const locationName = await resolveLocationName(latitude, longitude);

      saveLocation(latitude, longitude, locationName);
      label.textContent = locationName;
      button.title = 'Using your current location';
      button.disabled = false;
    }, (error) => {
      label.textContent = localStorage.getItem('locationName') || 'Location unavailable';
      button.title = error.message || 'Unable to access your location.';
      button.disabled = false;
    }, { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 });
  });
}

function initNotifications() {
  const toggle = document.getElementById('notification-toggle');
  const menu = document.getElementById('notification-menu');
  const items = document.getElementById('notification-items');
  const count = document.getElementById('notification-count');
  if (!toggle || !menu || !items || !count) return;

  const readIds = new Set(JSON.parse(localStorage.getItem('readNotifications') || '[]'));
  fetch('/api/notifications')
    .then((response) => {
      if (!response.ok) throw new Error(`Notification request failed (${response.status})`);
      return response.json();
    })
    .then((data) => {
      const notifications = data.items || [];
      count.textContent = String(notifications.filter((item) => !readIds.has(item.id)).length);
      if (!notifications.length) {
        items.innerHTML = '<p class="notification-empty">You are all caught up.</p>';
        return;
      }

      notifications.forEach((notification) => {
        const entry = document.createElement('button');
        entry.type = 'button';
        entry.className = `notification-item${readIds.has(notification.id) ? ' is-read' : ''}`;
        const title = document.createElement('strong');
        title.textContent = notification.title;
        const detail = document.createElement('small');
        detail.textContent = `${notification.severity} · ${notification.location} · ${notification.time}`;
        entry.append(title, detail);
        entry.addEventListener('click', () => {
          readIds.add(notification.id);
          localStorage.setItem('readNotifications', JSON.stringify([...readIds]));
          entry.classList.add('is-read');
          count.textContent = String(Math.max(0, Number(count.textContent) - 1));
        });
        items.append(entry);
      });
    })
    .catch((error) => {
      console.error('Failed to load notifications:', error);
      items.innerHTML = '<p class="notification-empty">Notifications are unavailable right now.</p>';
      count.textContent = '!';
    });

  toggle.addEventListener('click', () => {
    menu.hidden = !menu.hidden;
    toggle.setAttribute('aria-expanded', String(!menu.hidden));
  });
  document.addEventListener('click', (event) => {
    if (!event.target.closest('.notification-wrap')) {
      menu.hidden = true;
      toggle.setAttribute('aria-expanded', 'false');
    }
  });
}

async function resolveLocationName(latitude, longitude) {
  try {
    const params = new URLSearchParams({
      lat: latitude,
      lon: longitude,
      format: 'jsonv2',
      zoom: '10',
      addressdetails: '1',
    });
    const response = await fetch(`https://nominatim.openstreetmap.org/reverse?${params}`);
    if (!response.ok) throw new Error(`Reverse geocoding failed (${response.status})`);
    const place = await response.json();
    const address = place.address || {};
    const locality = address.city || address.town || address.village || address.municipality ||
      address.suburb || address.county || address.state_district || address.state;
    return [locality, address.country].filter(Boolean).join(', ') || 'Nearby location';
  } catch (error) {
    console.warn('Reverse geocoding unavailable; using a generic location label.', error);
    return 'Nearby location';
  }
}

function saveLocation(latitude, longitude, name) {
  localStorage.setItem('locationLatitude', latitude.toString());
  localStorage.setItem('locationLongitude', longitude.toString());
  localStorage.setItem('locationName', name);
  const locationLabel = document.getElementById('current-location-label');
  if (locationLabel) locationLabel.textContent = name;
  window.dispatchEvent(new CustomEvent('disasterguard:location-changed', {
    detail: { latitude, longitude, name },
  }));
}

function initDashboard() {
  const dashboardEl = document.getElementById('dashboard-page');
  if (!dashboardEl) return;

  fetch('/api/dashboard-summary')
    .then((response) => response.json())
    .then((data) => {
      const mapping = {
        'stat-alerts': data.cards[0]?.value,
        'stat-risk-areas': data.cards[1]?.value,
        'stat-monitored': data.cards[2]?.value,
        'stat-weather-stations': data.cards[3]?.value,
        'stat-incidents': data.cards[4]?.value,
        'stat-data-availability': data.cards[5]?.value,
      };

      Object.entries(mapping).forEach(([id, value]) => {
        const node = document.getElementById(id);
        if (node) node.textContent = value || '--';
      });
      loadDashboardWeather();

      const alertList = document.getElementById('alert-list');
      if (alertList) {
        alertList.innerHTML = data.alerts.map((item) => `
          <div class="alert-item">
            <div>
              <h4>${item.title}</h4>
              <div class="alert-meta">${item.time}</div>
            </div>
            <span class="severity-chip ${item.severity === 'High' || item.severity === 'Warning' ? 'high' : 'normal'}">${item.severity}</span>
          </div>
        `).join('');
      }

      const locationList = document.getElementById('location-list');
      if (locationList) {
        locationList.innerHTML = data.risk_locations.map((location) => `
          <div class="location-item">
            <div>
              <h4>${location.name}</h4>
              <div class="location-meta">Lat ${location.lat.toFixed(2)} • Lng ${location.lng.toFixed(2)}</div>
            </div>
            <span class="severity-chip ${location.risk === 'Critical' ? 'high' : 'normal'}">${location.risk}</span>
          </div>
        `).join('');
      }

      const eventsTable = document.getElementById('events-table');
      if (eventsTable) {
        eventsTable.innerHTML = [
          { title: 'Severe rainfall warning', zone: 'Sylhet Division', time: '09:25' },
          { title: 'Cyclone path adjustment', zone: 'Cox’s Bazar', time: '08:40' },
          { title: 'Hill slope instability', zone: 'Khagrachhari', time: '07:50' },
          { title: 'River level escalation', zone: 'Faridpur', time: '07:10' },
        ].map((event) => `
          <div class="event-row">
            <strong>${event.title}</strong>
            <span>${event.zone}</span>
            <span>${event.time}</span>
          </div>
        `).join('');
      }

      const activityList = document.getElementById('activity-list');
      if (activityList) {
        activityList.innerHTML = [
          'Alert threshold exceeded at Sunamganj',
          'Model retraining completed for coastal winds',
          'Station calibration passed in Khulna',
          'Daily public advisory distributed',
        ].map((entry) => `<div class="activity-item"><h4>${entry}</h4><span class="alert-meta">5 min ago</span></div>`).join('');
      }

      const healthStack = document.getElementById('health-stack');
      if (healthStack) {
        healthStack.innerHTML = [
          ['Weather API', 'Online'],
          ['GIS layers', 'Connected'],
          ['Flood engine', 'Stable'],
          ['Alert pipeline', 'Healthy'],
        ].map(([label, value]) => `<div class="health-item"><span>${label}</span><strong>${value}</strong></div>`).join('');
      }

      renderCharts(data);
      initMap('dashboard-map', [
        { name: 'Sunamganj', risk: 'Critical', lat: 25.07, lng: 91.4 },
        { name: 'Cox\'s Bazar', risk: 'High', lat: 21.42, lng: 91.98 },
        { name: 'Khagrachhari', risk: 'Moderate', lat: 23.1, lng: 91.97 },
      ]);
    })
    .catch((error) => console.error('Failed to fetch dashboard summary:', error));
}

function renderCharts(summary) {
  const alertTypes = ['Flood', 'Cyclone', 'Weather', 'Landslide'];
  const alertCounts = alertTypes.map((type) =>
    (summary.alerts || []).filter((alert) => alert.hazard === type).length
  );
  const riskTypes = ['Low', 'Moderate', 'High', 'Critical'];
  const riskCounts = riskTypes.map((type) =>
    (summary.risk_locations || []).filter((location) => location.risk.toLowerCase() === type.toLowerCase()).length
  );
  const chartConfigs = [
    { id: 'frequencyChart', type: 'bar', labels: alertTypes, values: alertCounts, color: '#d54141', axisLabel: 'Alerts in demo feed', max: Math.max(3, ...alertCounts) + 1 },
    { id: 'hazardChart', type: 'bar', labels: (summary.risk_locations || []).map((location) => location.name), values: (summary.risk_locations || []).map((location) => location.risk === 'Critical' ? 4 : location.risk === 'High' ? 3 : location.risk === 'Moderate' ? 2 : 1), color: '#ee9a25', axisLabel: 'Illustrative risk score (1–4)', max: 5 },
    { id: 'riskChart', type: 'bar', labels: riskTypes, values: riskCounts, color: '#2db07d', axisLabel: 'Mapped demo locations', max: Math.max(3, ...riskCounts) + 1 },
    { id: 'historyChart', type: 'radar', labels: ['Predictive', 'Observed', 'Recovery', 'Warning', 'Response', 'Resilience'], values: [65, 75, 58, 82, 70, 77], color: '#0d4d6a', max: 100 },
  ];

  chartConfigs.forEach(({ id, type, labels, values, color, axisLabel, max }) => {
    const canvas = document.getElementById(id);
    if (!canvas) return;
    Chart.getChart(canvas)?.destroy();

    const dataset = {
      label: axisLabel || 'Illustrative model score',
      data: values,
      backgroundColor: type === 'radar' ? 'rgba(26, 166, 160, 0.22)' : 'rgba(26, 166, 160, 0.72)',
      borderColor: color,
      borderWidth: 2,
      borderRadius: type === 'bar' ? 6 : 0,
      fill: type === 'radar',
      pointRadius: type === 'radar' ? 4 : 0,
    };

    const dataValueLabels = {
      id: 'radarValueLabels',
      afterDatasetsDraw(chart) {
        const { ctx } = chart;
        const textColor = getComputedStyle(document.body).getPropertyValue('--text').trim();
        ctx.save();
        ctx.font = '700 11px Inter, sans-serif';
        if (chart.config.type === 'radar') {
          const meta = chart.getDatasetMeta(0);
          const values = chart.data.datasets[0].data;
          const { chartArea } = chart;
          const centerX = (chartArea.left + chartArea.right) / 2;
          const centerY = (chartArea.top + chartArea.bottom) / 2;
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          meta.data.forEach((point, index) => {
            const position = point.getProps(['x', 'y'], true);
            const dx = position.x - centerX;
            const dy = position.y - centerY;
            const length = Math.hypot(dx, dy) || 1;
            const x = position.x;
            const y = position.y;
            const value = String(values[index]);
            const width = ctx.measureText(value).width + 12;
            ctx.fillStyle = getComputedStyle(document.body).getPropertyValue('--panel-alt').trim();
            ctx.beginPath();
            ctx.roundRect(x - width / 2, y - 9, width, 18, 6);
            ctx.fill();
            ctx.fillStyle = textColor;
            ctx.fillText(value, x, y);
          });
        } else if (chart.config.type === 'bar') {
          const meta = chart.getDatasetMeta(0);
          ctx.textAlign = 'left';
          ctx.textBaseline = 'middle';
          ctx.fillStyle = textColor;
          meta.data.forEach((bar, index) => {
            const { x, y } = bar.getProps(['x', 'y'], true);
            ctx.fillText(String(chart.data.datasets[0].data[index]), x + 7, y);
          });
        }
        ctx.restore();
      },
    };

    new Chart(canvas, {
      type,
      data: {
        labels,
        datasets: [dataset],
      },
      plugins: [dataValueLabels],
      options: {
        responsive: true,
        maintainAspectRatio: false,
        layout: { padding: type === 'radar' ? { top: 16, right: 24, bottom: 18, left: 24 } : 4 },
        plugins: { legend: { display: false }, tooltip: { enabled: true } },
        indexAxis: type === 'bar' ? 'y' : 'x',
        scales: type === 'bar' ? {
          x: {
            beginAtZero: true,
            max,
            ticks: { precision: 0, stepSize: 1 },
            title: { display: true, text: axisLabel },
          },
          y: { grid: { display: false } },
        } : type === 'radar' ? {
          r: {
            min: 0,
            max: 100,
            ticks: {
              stepSize: 25,
              display: true,
              showLabelBackdrop: false,
              backdropColor: 'transparent',
              font: { size: 9 },
              callback: (value) => value === 0 || value === 100 ? value : '',
            },
            pointLabels: { padding: 14, font: { size: 10, weight: '600' } },
            angleLines: { color: 'rgba(120, 140, 160, 0.2)' },
            grid: { color: 'rgba(120, 140, 160, 0.18)' },
          },
        } : undefined,
      },
    });
  });
}

function loadDashboardWeather() {
  const locationName = localStorage.getItem('locationName') || 'Dhaka, Bangladesh';
  const latitude = localStorage.getItem('locationLatitude') || '23.8103';
  const longitude = localStorage.getItem('locationLongitude') || '90.4125';
  const params = new URLSearchParams({ lat: latitude, lon: longitude, location_name: locationName });
  fetch(`/api/weather-data?${params}`)
    .then((response) => {
      if (!response.ok) throw new Error(`Weather request failed (${response.status})`);
      return response.json();
    })
    .then((data) => {
      const current = data.current || {};
      const feedStatus = data.source === 'Open-Meteo' ? 'Connected' : 'Demo';
      const sourceStatus = data.source === 'Open-Meteo' ? 'Open-Meteo' : 'Demo';
      const values = {
        'dashboard-weather-location': data.location || locationName,
        'dashboard-weather-status': data.status === 'Live' ? 'Live weather feed' : 'Demo weather data',
        'dashboard-temperature': current.temperature == null ? '--' : `${current.temperature}°C`,
        'dashboard-condition': current.condition || 'Conditions unavailable',
        'dashboard-humidity': current.humidity == null ? '--' : `${current.humidity}%`,
        'dashboard-rainfall': current.rainfall == null ? '--' : `${current.rainfall} mm`,
        'dashboard-wind': current.wind_speed == null ? '--' : `${current.wind_speed} km/h`,
        'dashboard-pressure': current.pressure == null ? '--' : `${current.pressure} hPa`,
        'stat-weather-stations': feedStatus,
        'stat-data-availability': sourceStatus,
      };
      Object.entries(values).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) element.textContent = value;
      });
      renderWeatherTrendCharts(data);
    })
    .catch((error) => console.error('Failed to load dashboard weather:', error));
}

function formatForecastTime(value, options) {
  const dateTime = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(value) ? `${value}:00Z` : value;
  const dateOnly = /^\d{4}-\d{2}-\d{2}$/.test(dateTime);
  const date = new Date(dateOnly ? `${dateTime}T12:00:00Z` : dateTime);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, { ...options, timeZone: 'UTC' }).format(date);
}

function renderWeatherTrendCharts(weather) {
  const sourceLabel = weather.source === 'Open-Meteo' ? 'Open-Meteo' : 'Demo data';
  ['rainfall-chart-source', 'temperature-chart-source'].forEach((id) => {
    const source = document.getElementById(id);
    if (source) source.textContent = sourceLabel;
  });
  const chartSpecs = [
    {
      id: 'rainfallChart',
      label: 'Precipitation (mm)',
      values: (weather.hourly || []).map((item) => item.precipitation ?? 0),
      color: '#1aa6a0',
      unit: 'mm',
    },
    {
      id: 'temperatureChart',
      label: 'Temperature (°C)',
      values: (weather.hourly || []).map((item) => item.temp),
      color: '#4577d7',
      unit: '°C',
    },
  ];
  chartSpecs.forEach(({ id, label, values, color, unit }) => {
    const canvas = document.getElementById(id);
    if (!canvas || !values.length) return;
    Chart.getChart(canvas)?.destroy();
    new Chart(canvas, {
      type: 'line',
      data: {
        labels: (weather.hourly || []).map((item) => formatForecastTime(item.time, { hour: 'numeric' })),
        datasets: [{
          label,
          data: values,
          borderColor: color,
          backgroundColor: `${color}26`,
          fill: true,
          tension: 0.32,
          pointRadius: 2,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: true } },
        scales: {
          y: {
            beginAtZero: unit === 'mm',
            title: { display: true, text: unit },
            ticks: { precision: unit === 'mm' ? 1 : 0 },
          },
        },
      },
    });
  });
}

function initWeather() {
  const weatherPage = document.getElementById('weather-page');
  if (!weatherPage) return;

  const latitudeInput = document.getElementById('lat-input');
  const longitudeInput = document.getElementById('lon-input');
  const manualFields = document.getElementById('manual-location-fields');
  const modeStatus = document.getElementById('location-mode-status');
  const automaticModeButton = document.getElementById('automatic-location-mode');
  const manualModeButton = document.getElementById('manual-location-mode');
  const storedLatitude = localStorage.getItem('locationLatitude');
  const storedLongitude = localStorage.getItem('locationLongitude');
  const storedName = localStorage.getItem('locationName');
  if (latitudeInput && longitudeInput) {
    latitudeInput.value = storedLatitude || '23.8103';
    longitudeInput.value = storedLongitude || '90.4125';
  }
  let selectedLocationName = storedName || 'Dhaka, Bangladesh';
  let refreshSequence = 0;
  let modeRequestSequence = 0;

  const refresh = async () => {
    const lat = latitudeInput?.value;
    const lon = longitudeInput?.value;
    if (!Number.isFinite(Number(lat)) || !Number.isFinite(Number(lon)) ||
        Number(lat) < -90 || Number(lat) > 90 || Number(lon) < -180 || Number(lon) > 180) {
      document.getElementById('weather-status').textContent = 'Enter valid coordinates';
      return;
    }
    const sequence = ++refreshSequence;
    void loadLocationPrediction(lat, lon, selectedLocationName);
    void loadLocationHazards(lat, lon);

    try {
      document.getElementById('weather-status').textContent = 'Loading weather...';
      const params = new URLSearchParams({ lat, lon, location_name: selectedLocationName });
      const response = await fetch(`/api/weather-data?${params}`);
      if (!response.ok) throw new Error(`Weather API request failed (${response.status})`);
      const data = await response.json();
      if (sequence !== refreshSequence) return;

      document.getElementById('weather-status').textContent = data.status || 'Demo mode';
      document.getElementById('weather-source').textContent = data.source || 'Demo source';
      document.getElementById('weather-location').textContent = selectedLocationName;
      document.getElementById('temperature-value').textContent = Number.isFinite(data.current?.temperature) ? `${data.current.temperature.toFixed(1)}°C` : '--';
      document.getElementById('weather-condition').textContent = data.current?.condition || 'Current conditions';
      document.getElementById('humidity-value').textContent = Number.isFinite(data.current?.humidity) ? `${data.current.humidity}%` : '--';
      document.getElementById('rainfall-value').textContent = Number.isFinite(data.current?.rainfall) ? `${data.current.rainfall} mm` : '--';
      document.getElementById('wind-speed-value').textContent = Number.isFinite(data.current?.wind_speed) ? `${data.current.wind_speed} km/h` : '--';
      document.getElementById('pressure-value').textContent = Number.isFinite(data.current?.pressure) ? `${data.current.pressure} hPa` : '--';
      document.getElementById('last-updated').textContent = data.last_updated || '--';

      const hourly = document.getElementById('hourly-forecast');
      if (hourly) {
        hourly.innerHTML = (data.hourly || []).map((item) => `
          <div class="forecast-item">
            <span>${formatForecastTime(item.time, { hour: 'numeric' })}</span>
            <strong>${item.temp}°C</strong>
            <span>${item.rain}% rain</span>
          </div>
        `).join('');
      }

      const daily = document.getElementById('daily-forecast');
      if (daily) {
        daily.innerHTML = (data.daily || []).map((item) => `
          <div class="forecast-item">
            <span>${formatForecastTime(item.day, { weekday: 'short' })}</span>
            <strong>${item.max}° / ${item.min}°</strong>
            <span>${item.rain} mm</span>
          </div>
        `).join('');
      }

      const rainfallChart = document.getElementById('weatherRainChart');
      if (rainfallChart) {
        const chart = Chart.getChart(rainfallChart);
        if (chart) chart.destroy();

        new Chart(rainfallChart, {
          type: 'bar',
          data: {
            labels: (data.hourly || []).map((item) => item.time),
            datasets: [{
              label: 'Rain probability',
              data: (data.hourly || []).map((item) => item.rain || 0),
              backgroundColor: 'rgba(29, 166, 160, 0.75)',
              borderRadius: 8,
            }],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { y: { beginAtZero: true } },
          },
        });
      }
    } catch (error) {
      console.error('Weather fetch failed', error);
      if (sequence !== refreshSequence) return;
      document.getElementById('weather-status').textContent = 'Weather unavailable';
    }
  };

  const setMode = (mode) => {
    const automatic = mode === 'automatic';
    if (manualFields) manualFields.hidden = automatic;
    automaticModeButton?.setAttribute('aria-pressed', String(automatic));
    manualModeButton?.setAttribute('aria-pressed', String(!automatic));
    localStorage.setItem('locationMode', mode);
  };

  const useAutomaticLocation = () => {
    const requestSequence = ++modeRequestSequence;
    setMode('automatic');
    if (!navigator.geolocation) {
      if (modeStatus) modeStatus.textContent = 'Device location is not available. Showing your saved location instead.';
      void refresh();
      return;
    }

    if (modeStatus) modeStatus.textContent = 'Finding your location…';
    navigator.geolocation.getCurrentPosition(async (position) => {
      const { latitude, longitude } = position.coords;
      const locationName = await resolveLocationName(latitude, longitude);
      if (requestSequence !== modeRequestSequence) return;
      selectedLocationName = locationName;
      if (modeStatus) modeStatus.textContent = 'Using your current location. Forecasts update automatically.';
      saveLocation(latitude, longitude, selectedLocationName);
    }, (error) => {
      if (requestSequence !== modeRequestSequence) return;
      console.warn('Automatic location unavailable:', error.message);
      if (modeStatus) modeStatus.textContent = 'Location access unavailable. Showing your saved or default location; you can choose a place manually.';
      void refresh();
    }, { enableHighAccuracy: false, timeout: 12000, maximumAge: 300000 });
  };

  const useManualLocation = async () => {
    const requestSequence = ++modeRequestSequence;
    const placeInput = document.getElementById('place-input');
    const query = placeInput?.value.trim();
    const status = document.getElementById('weather-status');
    let latitude = Number(latitudeInput?.value);
    let longitude = Number(longitudeInput?.value);

    if (query) {
      status.textContent = 'Finding place…';
      try {
        const params = new URLSearchParams({ name: query, count: '1', language: 'en', format: 'json' });
        const response = await fetch(`https://geocoding-api.open-meteo.com/v1/search?${params}`);
        if (!response.ok) throw new Error(`Location search failed (${response.status})`);
        const result = await response.json();
        if (requestSequence !== modeRequestSequence) return;
        const place = result.results?.[0];
        if (!place) throw new Error('Location not found. Try a nearby city or enter coordinates.');
        latitude = place.latitude;
        longitude = place.longitude;
        selectedLocationName = [place.name, place.admin1, place.country].filter(Boolean).join(', ');
        latitudeInput.value = String(latitude);
        longitudeInput.value = String(longitude);
      } catch (error) {
        if (requestSequence !== modeRequestSequence) return;
        console.error('Location search failed:', error);
        status.textContent = error.message || 'Location search unavailable';
        return;
      }
    } else {
      if (!Number.isFinite(latitude) || !Number.isFinite(longitude) ||
          latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) {
        status.textContent = 'Enter a place name or valid coordinates';
        return;
      }
      selectedLocationName = await resolveLocationName(latitude, longitude);
      if (requestSequence !== modeRequestSequence) return;
    }

    if (requestSequence !== modeRequestSequence) return;
    setMode('manual');
    if (modeStatus) modeStatus.textContent = `Using manually selected location: ${selectedLocationName}`;
    saveLocation(latitude, longitude, selectedLocationName);
  };

  automaticModeButton?.addEventListener('click', useAutomaticLocation);
  manualModeButton?.addEventListener('click', () => {
    modeRequestSequence += 1;
    setMode('manual');
    if (modeStatus) modeStatus.textContent = 'Search for a place or enter its coordinates, then show its outlook.';
  });
  document.getElementById('apply-manual-location')?.addEventListener('click', useManualLocation);
  document.getElementById('place-input')?.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') useManualLocation();
  });

  window.addEventListener('disasterguard:location-changed', (event) => {
    const { latitude, longitude, name } = event.detail;
    latitudeInput.value = latitude;
    longitudeInput.value = longitude;
    selectedLocationName = name;
    if (localStorage.getItem('locationMode') === 'automatic' && modeStatus) {
      modeStatus.textContent = `Using your current location: ${name}`;
    }
    void refresh();
  });

  const initialMode = localStorage.getItem('locationMode') || 'automatic';
  if (initialMode === 'manual') {
    setMode('manual');
    if (modeStatus) modeStatus.textContent = 'Using your saved location. Choose a place or enter coordinates to update it.';
    void refresh();
  } else {
    useAutomaticLocation();
  }
}

let activeLocationPrediction = 0;
let activeLocationHazardRequest = 0;

async function loadLocationPrediction(latitude, longitude, locationName) {
  const status = document.getElementById('location-risk-status');
  const results = document.getElementById('location-risk-results');
  const disclaimer = document.getElementById('location-risk-disclaimer');
  if (!status || !results) return;

  const requestId = ++activeLocationPrediction;
  status.textContent = 'Loading live weather and terrain data…';
  results.replaceChildren();

  try {
    const response = await fetch('/api/predict/location', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        latitude: Number(latitude),
        longitude: Number(longitude),
        location: locationName,
      }),
    });
    const prediction = await response.json();
    if (!response.ok) throw new Error(prediction.error || `Prediction request failed (${response.status})`);
    if (requestId !== activeLocationPrediction) return;

    prediction.risks.forEach((risk) => {
      const card = document.createElement('article');
      card.className = 'location-risk-card';
      const icon = document.createElement('i');
      icon.className = `fa-solid ${risk.hazard.toLowerCase().includes('flood') ? 'fa-water' : 'fa-mountain-sun'}`;
      icon.setAttribute('aria-hidden', 'true');
      const heading = document.createElement('h4');
      heading.textContent = risk.hazard;
      const value = document.createElement('strong');
      value.className = 'location-risk-value';
      value.textContent = `${risk.risk_index_percent}%`;
      const category = document.createElement('p');
      category.textContent = `${risk.category} relative risk index`;
      const factors = document.createElement('p');
      factors.textContent = risk.factors.join(' · ');
      card.append(icon, heading, value, category, factors);
      results.append(card);
    });

    status.textContent = `${prediction.cached ? 'Cached forecast' : 'Updated'} from ${prediction.source} · ${prediction.forecast_horizon}`;
    if (disclaimer) disclaimer.textContent = prediction.disclaimer;
  } catch (error) {
    if (requestId !== activeLocationPrediction) return;
    console.error('Location risk update failed:', error);
    status.textContent = error.message || 'Live location risk data is unavailable.';
  }
}

async function loadLocationHazards(latitude, longitude) {
  const status = document.getElementById('location-observation-status');
  const cycloneList = document.getElementById('nearby-cyclones');
  const earthquakeList = document.getElementById('nearby-earthquakes');
  if (!status || !cycloneList || !earthquakeList) return;

  const requestId = ++activeLocationHazardRequest;
  status.textContent = 'Checking nearby cyclone and earthquake feeds…';
  cycloneList.replaceChildren();
  earthquakeList.replaceChildren();

  try {
    const response = await fetch('/api/hazards/location', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        latitude: Number(latitude),
        longitude: Number(longitude),
      }),
    });
    const hazards = await response.json();
    if (!response.ok) throw new Error(hazards.error || `Nearby hazard request failed (${response.status})`);
    if (requestId !== activeLocationHazardRequest) return;

    if (hazards.cyclone_status === 'live') {
      if (!hazards.cyclones.length) {
        appendHazardEmptyState(
          cycloneList,
          `No active GDACS cyclone event center was found within ${hazards.cyclone_radius_km} km. This does not guarantee safety.`
        );
      } else {
        hazards.cyclones.forEach((cyclone) => {
          const entry = document.createElement('article');
          entry.className = 'observed-hazard-entry';
          const title = document.createElement('strong');
          title.textContent = cyclone.name;
          const details = document.createElement('p');
          details.textContent = `${cyclone.alert_level} alert · ${cyclone.distance_km} km from the reported event center${cyclone.affected_countries ? ` · ${cyclone.affected_countries}` : ''}`;
          entry.append(title, details);
          appendTrustedEventLink(entry, cyclone.url, 'View GDACS report');
          cycloneList.append(entry);
        });
      }
    } else {
      appendHazardEmptyState(cycloneList, 'GDACS cyclone reports are temporarily unavailable.');
    }

    if (hazards.earthquake_status === 'live') {
      if (!hazards.earthquakes.length) {
        appendHazardEmptyState(
          earthquakeList,
          `No USGS earthquakes were reported within ${hazards.earthquake_radius_km} km in the last ${hazards.earthquake_days} days. Earthquakes cannot be predicted.`
        );
      } else {
        hazards.earthquakes.forEach((earthquake) => {
          const entry = document.createElement('article');
          entry.className = 'observed-hazard-entry';
          const title = document.createElement('strong');
          title.textContent = Number.isFinite(earthquake.magnitude)
            ? `Magnitude ${earthquake.magnitude.toFixed(1)}`
            : 'Magnitude not reported';
          const details = document.createElement('p');
          const occurred = Number.isFinite(earthquake.time)
            ? new Date(earthquake.time).toLocaleString()
            : 'Time not reported';
          details.textContent = `${earthquake.place} · ${earthquake.distance_km} km away · ${earthquake.depth_km} km deep · ${occurred}`;
          entry.append(title, details);
          appendTrustedEventLink(entry, earthquake.url, 'View USGS event');
          earthquakeList.append(entry);
        });
      }
    } else {
      appendHazardEmptyState(earthquakeList, 'USGS earthquake reports are temporarily unavailable.');
    }

    const sourceStatus = [
      `GDACS ${hazards.cyclone_status}`,
      `USGS ${hazards.earthquake_status}`,
    ].join(' · ');
    status.textContent = `${hazards.cached ? 'Recent cached check' : 'Nearby event check complete'} · ${sourceStatus}`;
  } catch (error) {
    if (requestId !== activeLocationHazardRequest) return;
    console.error('Nearby hazard feeds unavailable:', error);
    appendHazardEmptyState(cycloneList, 'Cyclone event data is unavailable.');
    appendHazardEmptyState(earthquakeList, 'Earthquake event data is unavailable.');
    status.textContent = error.message || 'Nearby hazard feeds are unavailable.';
  }
}

function appendHazardEmptyState(container, message) {
  const empty = document.createElement('p');
  empty.className = 'observed-hazard-empty';
  empty.textContent = message;
  container.append(empty);
}

function appendTrustedEventLink(container, href, label) {
  if (!href) return;
  const link = document.createElement('a');
  link.href = href;
  link.target = '_blank';
  link.rel = 'noopener noreferrer';
  link.textContent = label;
  container.append(link);
}

function initFloodPrediction() {
  const form = document.getElementById('flood-form');
  if (!form) return;

  if (new URLSearchParams(window.location.search).has('predict')) {
    setTimeout(() => { form.dispatchEvent(new Event('submit')); }, 500);
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());

    const response = await fetch('/api/predict/flood', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const result = await response.json();
    document.getElementById('risk-probability').textContent = `${result.flood_probability ?? '--'}%`;
    document.getElementById('risk-category').textContent = result.risk_category || '--';
    document.getElementById('risk-explanation').textContent = result.risk_explanation || 'No explanation available';
    document.getElementById('risk-factors').textContent = Array.isArray(result.contributing_factors) ? result.contributing_factors.join(', ') : '--';
  });
}

function initModulePrediction() {
  const form = document.querySelector('.module-prediction-form');
  if (!form) return;
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const submit = form.querySelector('button[type="submit"]');
    submit.disabled = true;
    submit.textContent = 'Calculating…';
    try {
      const response = await fetch(`/api/predict/${form.dataset.hazard}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(Object.fromEntries(new FormData(form).entries())),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || `Prediction request failed (${response.status})`);
      document.getElementById('module-risk-probability').textContent = `${result.flood_probability}% probability`;
      document.getElementById('module-risk-category').textContent = result.risk_category;
      document.getElementById('module-risk-explanation').textContent = result.risk_explanation;
      document.getElementById('module-risk-factors').textContent = result.contributing_factors.join(', ');
      document.querySelector('#module-prediction-result .status-pill').textContent = result.status;
    } catch (error) {
      console.error('Prediction request failed:', error);
      document.getElementById('module-risk-explanation').textContent = error.message;
    } finally {
      submit.disabled = false;
      submit.textContent = 'Run demo assessment';
    }
  });
}

function initModuleAnalytics() {
  const canvas = document.getElementById('module-analytics-chart');
  if (!canvas) return;
  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: ['Flood', 'Cyclone', 'Landslide'],
      datasets: [{ label: 'Illustrative assessments', data: [42, 30, 18], backgroundColor: ['#188b99', '#ed9b37', '#497bd2'], borderRadius: 8 }],
    },
    options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, max: 50, ticks: { stepSize: 10 } } } },
  });
}

function initReportExport() {
  const button = document.getElementById('export-report');
  const status = document.getElementById('export-status');
  if (!button || !status) return;

  button.addEventListener('click', async () => {
    button.disabled = true;
    status.textContent = 'Preparing report…';
    try {
      const response = await fetch('/api/dashboard-summary');
      if (!response.ok) throw new Error(`Report data request failed (${response.status})`);
      const summary = await response.json();
      const report = {
        generated_at: new Date().toISOString(),
        data_source: summary.data_source,
        demo_mode: true,
        status: summary.status,
        metrics: summary.cards,
        alerts: summary.alerts,
        high_risk_locations: summary.risk_locations,
        recent_events: summary.recent_events,
      };
      const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' }));
      const link = document.createElement('a');
      link.href = url;
      link.download = `disasterguard-report-${new Date().toISOString().slice(0, 10)}.json`;
      link.click();
      URL.revokeObjectURL(url);
      status.textContent = 'Report downloaded';
    } catch (error) {
      console.error('Report export failed:', error);
      status.textContent = error.message;
    } finally {
      button.disabled = false;
    }
  });
}

function initMap(id = 'risk-map', points = []) {
  const mapTarget = document.getElementById(id);
  if (!mapTarget) return;

  const map = L.map(mapTarget, { zoomControl: true }).setView([23.7, 90.89], 7);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '&copy; OpenStreetMap contributors',
  }).addTo(map);

  const defaultPoints = [
    { name: 'Sunamganj', risk: 'Critical', lat: 25.07, lng: 91.4 },
    { name: 'Cox\'s Bazar', risk: 'High', lat: 21.42, lng: 91.98 },
    { name: 'Khagrachhari', risk: 'Moderate', lat: 23.1, lng: 91.97 },
  ];

  const markerPoints = points.length ? points : defaultPoints;
  markerPoints.forEach((point) => {
    const color = point.risk === 'Critical' ? '#d54141' : point.risk === 'High' ? '#ee9a25' : point.risk === 'Moderate' ? '#3ca1d9' : '#2db07d';
    L.circleMarker([point.lat, point.lng], {
      radius: 12,
      color,
      fillColor: color,
      fillOpacity: 0.7,
    }).addTo(map).bindPopup(`<strong>${point.name}</strong><br/>${point.risk} risk`);
  });
}
