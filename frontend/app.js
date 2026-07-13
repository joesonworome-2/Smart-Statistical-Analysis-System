(() => {
  const sampleCsv = [
    'region,year,patients,screenings,positive_cases,recovery_days,satisfaction,cost_usd',
    'Port Moresby,2021,410,320,42,18,84,24100',
    'Lae,2021,365,260,39,20,78,21900',
    'Madang,2021,220,160,22,24,81,13700',
    'Goroka,2021,198,150,18,21,86,12800',
    'Port Moresby,2022,438,350,47,16,88,25350',
    'Lae,2022,382,286,41,18,80,22880',
    'Madang,2022,248,190,25,20,83,15120',
    'Goroka,2022,205,172,16,19,89,13250',
    'Port Moresby,2023,470,392,51,14,91,26900',
    'Lae,2023,401,320,44,17,84,23940',
    'Madang,2023,265,211,27,19,85,16050',
    'Goroka,2023,226,198,19,18,90,14500'
  ].join('\n');

  const state = {
    name: '',
    columns: [],
    rows: [],
    numericColumns: [],
    filteredRows: [],
    lastResults: [],
    activeView: 'dashboard',
    filters: [],
    sortColumn: null,
    sortDirection: 'asc',
    transforms: [],
    originalRows: [],
    apiBaseUrl: 'http://127.0.0.1:8000/api',
    analysisHistory: []
  };

  const el = (id) => document.getElementById(id);
  const fmt = new Intl.NumberFormat('en-US');

  function showToast(message, type = 'info') {
    const container = el('toastRegion');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast ' + type;
    toast.textContent = message;
    container.appendChild(toast);

    requestAnimationFrame(() => toast.classList.add('visible'));
    window.setTimeout(() => {
      toast.classList.remove('visible');
      window.setTimeout(() => toast.remove(), 220);
    }, 2600);
  }

  function updateHeroPanel() {
    const status = el('workspaceStatus');
    const mode = el('heroMode');
    const readiness = el('heroReadiness');
    const signal = el('heroSignal');
    const copy = el('hero-copy');

    if (!status || !mode || !readiness || !signal || !copy) return;

    if (!state.rows.length) {
      status.textContent = 'Ready for your next dataset';
      status.className = 'status-pill neutral';
      mode.textContent = 'Discovery';
      readiness.textContent = 'Waiting for data';
      signal.textContent = '0 useful columns';
      copy.textContent = 'Upload a dataset, profile anomalies, refine features, and export polished analysis in minutes.';
      return;
    }

    const score = qualityScore();
    const scoreText = score === null ? 'Pending' : score + '%';
    status.textContent = `${state.rows.length} rows • ${state.columns.length} columns`;
    status.className = 'status-pill live';
    mode.textContent = state.numericColumns.length ? 'Ready for modeling' : 'Profiling';
    readiness.textContent = scoreText;
    signal.textContent = `${state.numericColumns.length} numeric fields`;
    copy.textContent = `${state.name || 'Loaded dataset'} is ready for deeper statistical review and export.`;
  }

  function parseDelimitedText(text, delimiter = ',') {
    const rows = [];
    let current = '';
    let row = [];
    let inQuotes = false;

    for (let i = 0; i < text.length; i += 1) {
      const char = text[i];
      const next = text[i + 1];

      if (char === '"' && inQuotes && next === '"') {
        current += '"';
        i += 1;
      } else if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === delimiter && !inQuotes) {
        row.push(current.trim());
        current = '';
      } else if ((char === '\n' || char === '\r') && !inQuotes) {
        if (char === '\r' && next === '\n') i += 1;
        row.push(current.trim());
        if (row.some((cell) => cell.length > 0)) rows.push(row);
        row = [];
        current = '';
      } else {
        current += char;
      }
    }

    row.push(current.trim());
    if (row.some((cell) => cell.length > 0)) rows.push(row);
    if (rows.length === 0) return { columns: [], rows: [] };

    const columns = rows[0].map((value, index) => value || 'Column ' + (index + 1));
    const dataRows = rows.slice(1).map((values) => {
      const record = {};
      columns.forEach((column, index) => {
        record[column] = values[index] ?? '';
      });
      return record;
    });

    return { columns, rows: dataRows };
  }

  function parseCsv(text) {
    return parseDelimitedText(text, ',');
  }

  function parseTsv(text) {
    return parseDelimitedText(text, '\t');
  }

  function loadWorkbookFile(file) {
    return file.arrayBuffer().then((buffer) => {
      const workbook = XLSX.read(buffer, { type: 'array' });
      const sheetName = workbook.SheetNames[0];
      if (!sheetName) return { columns: [], rows: [] };
      const sheet = workbook.Sheets[sheetName];
      const data = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '' });
      if (!data.length) return { columns: [], rows: [] };
      const columns = data[0].map((value, index) => String(value || 'Column ' + (index + 1)));
      const rows = data.slice(1).map((values) => {
        const record = {};
        columns.forEach((column, index) => {
          record[column] = values[index] ?? '';
        });
        return record;
      });
      return { columns, rows };
    });
  }

  function loadFile(file) {
    const name = file.name;
    const extension = name.split('.').pop().toLowerCase();

    if (extension === 'csv' || extension === 'txt') {
      return file.text().then((text) => {
        const parsed = parseCsv(text);
        setDataset(name, parsed.columns, parsed.rows);
      });
    }

    if (extension === 'tsv') {
      return file.text().then((text) => {
        const parsed = parseTsv(text);
        setDataset(name, parsed.columns, parsed.rows);
      });
    }

    if (extension === 'xls' || extension === 'xlsx') {
      return loadWorkbookFile(file).then((parsed) => {
        if (!parsed.columns.length) {
          window.alert('No data found in the Excel file.');
          return;
        }
        setDataset(name, parsed.columns, parsed.rows);
      }).catch((error) => {
        window.alert('Error reading Excel file: ' + error.message);
      });
    }

    if (extension === 'json') {
      return file.text().then((text) => {
        try {
          const json = JSON.parse(text);
          if (!Array.isArray(json) || json.length === 0 || typeof json[0] !== 'object') {
            throw new Error('JSON must be an array of objects.');
          }
          const columns = Object.keys(json[0]);
          const rows = json.map((item) => {
            const record = {};
            columns.forEach((column) => {
              record[column] = item[column] ?? '';
            });
            return record;
          });
          setDataset(name, columns, rows);
        } catch (error) {
          window.alert('Error parsing JSON file: ' + error.message);
        }
      });
    }

    return file.text().then((text) => {
      const parsed = parseCsv(text);
      if (!parsed.columns.length) {
        window.alert('Unsupported file format or no data found.');
        return;
      }
      setDataset(name, parsed.columns, parsed.rows);
    }).catch((error) => {
      window.alert('Unable to load file: ' + error.message);
    });
  }

  function isNumericValue(value) {
    if (value === null || value === undefined) return false;
    const cleaned = String(value).replace(/,/g, '').trim();
    return cleaned !== '' && Number.isFinite(Number(cleaned));
  }

  function toNumber(value) {
    const number = Number(String(value).replace(/,/g, '').trim());
    return Number.isFinite(number) ? number : null;
  }

  function getNumericValues(column) {
    return state.rows.map((row) => toNumber(row[column])).filter((value) => value !== null);
  }

  function detectNumericColumns() {
    state.numericColumns = state.columns.filter((column) => {
      const populated = state.rows.filter((row) => String(row[column] ?? '').trim() !== '');
      if (populated.length === 0) return false;
      const numeric = populated.filter((row) => isNumericValue(row[column]));
      return numeric.length / populated.length >= 0.65;
    });
  }

  function setDataset(name, columns, rows) {
    state.name = name;
    state.columns = columns;
    state.rows = rows;
    state.originalRows = JSON.parse(JSON.stringify(rows));
    state.filteredRows = rows;
    state.filters = [];
    state.sortColumn = null;
    state.sortDirection = 'asc';
    state.transforms = [];
    detectNumericColumns();
    state.lastResults = [];
    el('tableSearch').value = '';
    renderAll();
    setView('dashboard');
    showToast(`${name} loaded with ${rows.length} rows.`, 'success');
  }

  function clearDataset() {
    state.name = '';
    state.columns = [];
    state.rows = [];
    state.numericColumns = [];
    state.filteredRows = [];
    state.lastResults = [];
    renderAll();
    showToast('Workspace cleared. Load a new dataset to continue.', 'info');
  }

  function missingStats() {
    const total = state.rows.length * state.columns.length;
    const missing = state.rows.reduce((sum, row) => {
      return sum + state.columns.filter((column) => String(row[column] ?? '').trim() === '').length;
    }, 0);
    return { total, missing, rate: total ? missing / total : 0 };
  }

  function qualityScore() {
    if (!state.rows.length) return null;
    const stats = missingStats();
    const rowPenalty = state.rows.length < 30 ? 12 : 0;
    const numericPenalty = state.numericColumns.length < 2 ? 10 : 0;
    const score = Math.max(0, Math.round(100 - stats.rate * 100 - rowPenalty - numericPenalty));
    return score;
  }

  function renderMetrics() {
    const stats = missingStats();
    const score = qualityScore();
    const duplicates = countDuplicates();
    const outliers = countTotalOutliers();
    const typeConsistency = calculateTypeConsistency();
    const completeness = calculateCompleteness();
    
    el('rowCount').textContent = fmt.format(state.rows.length);
    el('rowDelta').textContent = state.name ? state.name : 'No dataset loaded';
    el('columnCount').textContent = fmt.format(state.columns.length);
    el('numericCount').textContent = fmt.format(state.numericColumns.length) + ' numeric fields';
    el('missingCount').textContent = fmt.format(stats.missing);
    el('missingRate').textContent = stats.total ? Math.round(stats.rate * 100) + '% of cells' : '0% of cells';
    el('qualityScore').textContent = score === null ? '--' : score + '%';
    el('qualityNote').textContent = score === null ? 'Waiting for data' : score >= 85 ? 'Ready for modeling' : score >= 70 ? 'Needs review' : 'Needs cleanup';
    el('duplicateCount').textContent = fmt.format(duplicates);
    el('duplicateRate').textContent = state.rows.length ? Math.round((duplicates / state.rows.length) * 100) + '% duplicate rows' : '0% duplicate rows';
    el('outlierCount').textContent = fmt.format(outliers);
    el('outlierRate').textContent = state.rows.length * state.numericColumns.length ? Math.round((outliers / (state.rows.length * state.numericColumns.length)) * 100) + '% of values' : '0% of values';
    el('typeConsistency').textContent = typeConsistency + '%';
    el('typeNote').textContent = typeConsistency >= 90 ? 'Excellent' : typeConsistency >= 70 ? 'Good' : 'Needs attention';
    el('completenessScore').textContent = completeness + '%';
    el('completenessNote').textContent = completeness >= 90 ? 'Complete' : completeness >= 70 ? 'Mostly complete' : 'Incomplete';
  }

  function renderSelects() {
    const numericOptions = state.numericColumns.length ? state.numericColumns : state.columns;
    const emptyOption = '<option value="">No columns available</option>';
    el('chartColumn').innerHTML = numericOptions.length ? numericOptions.map((column) => '<option value="' + escapeHtml(column) + '">' + escapeHtml(column) + '</option>').join('') : emptyOption;
    el('chartColumn2').innerHTML = numericOptions.length ? numericOptions.map((column) => '<option value="' + escapeHtml(column) + '">' + escapeHtml(column) + '</option>').join('') : emptyOption;
    el('targetColumn').innerHTML = numericOptions.length ? numericOptions.map((column) => '<option value="' + escapeHtml(column) + '">' + escapeHtml(column) + '</option>').join('') : emptyOption;
    el('filterColumn').innerHTML = state.columns.length ? state.columns.map((column) => '<option value="' + escapeHtml(column) + '">' + escapeHtml(column) + '</option>').join('') : '<option value="">Select column</option>';
    el('transformColumn').innerHTML = state.columns.length ? state.columns.map((column) => '<option value="' + escapeHtml(column) + '">' + escapeHtml(column) + '</option>').join('') : '<option value="">Select column</option>';
  }

  function renderTable() {
    el('datasetName').textContent = state.name || 'No dataset selected';
    const thead = el('dataTable').querySelector('thead');
    const tbody = el('dataTable').querySelector('tbody');

    if (!state.columns.length) {
      thead.innerHTML = '';
      tbody.innerHTML = '<tr><td class="empty-state">Load a dataset to preview records.</td></tr>';
      return;
    }

    thead.innerHTML = '<tr>' + state.columns.map((column) => {
      const sortIcon = state.sortColumn === column ? (state.sortDirection === 'asc' ? '&uarr;' : '&darr;') : '';
      return '<th style="cursor:pointer;" data-sort="' + escapeHtml(column) + '">' + escapeHtml(column) + ' ' + sortIcon + '</th>';
    }).join('') + '</tr>';
    
    applyFiltersAndSort();
    const previewRows = state.filteredRows.slice(0, 80);
    tbody.innerHTML = previewRows.map((row) => {
      return '<tr>' + state.columns.map((column) => '<td>' + escapeHtml(row[column] ?? '') + '</td>').join('') + '</tr>';
    }).join('');
    
    renderActiveFilters();
  }

  function renderActiveFilters() {
    const container = el('activeFilters');
    container.innerHTML = state.filters.map((filter, index) => {
      return '<span class="filter-tag">' + escapeHtml(filter.column) + ' ' + escapeHtml(filter.operator) + ' ' + escapeHtml(filter.value) + ' <button data-filter-index="' + index + '">&times;</button></span>';
    }).join('');
  }

  function applyFiltersAndSort() {
    let result = [...state.rows];
    
    state.filters.forEach((filter) => {
      result = result.filter((row) => {
        const value = String(row[filter.column] ?? '').toLowerCase();
        const filterValue = filter.value.toLowerCase();
        
        switch (filter.operator) {
          case 'contains':
            return value.includes(filterValue);
          case 'equals':
            return value === filterValue;
          case 'not_equals':
            return value !== filterValue;
          case 'greater':
            return toNumber(value) > toNumber(filterValue);
          case 'less':
            return toNumber(value) < toNumber(filterValue);
          case 'greater_equal':
            return toNumber(value) >= toNumber(filterValue);
          case 'less_equal':
            return toNumber(value) <= toNumber(filterValue);
          case 'empty':
            return value === '';
          case 'not_empty':
            return value !== '';
          default:
            return true;
        }
      });
    });
    
    if (state.sortColumn) {
      result.sort((a, b) => {
        const aVal = a[state.sortColumn];
        const bVal = b[state.sortColumn];
        const aNum = toNumber(aVal);
        const bNum = toNumber(bVal);
        
        if (aNum !== null && bNum !== null) {
          return state.sortDirection === 'asc' ? aNum - bNum : bNum - aNum;
        }
        
        const aStr = String(aVal ?? '').toLowerCase();
        const bStr = String(bVal ?? '').toLowerCase();
        return state.sortDirection === 'asc' ? aStr.localeCompare(bStr) : bStr.localeCompare(aStr);
      });
    }
    
    state.filteredRows = result;
  }

  function addFilter() {
    const column = el('filterColumn').value;
    const operator = el('filterOperator').value;
    const value = el('filterValue').value;
    
    if (!column) return;
    if (operator !== 'empty' && operator !== 'not_empty' && !value) return;
    
    state.filters.push({ column, operator, value });
    el('filterValue').value = '';
    renderTable();
  }

  function clearFilters() {
    state.filters = [];
    state.sortColumn = null;
    state.sortDirection = 'asc';
    renderTable();
  }

  function removeFilter(index) {
    state.filters.splice(index, 1);
    renderTable();
  }

  function handleSort(column) {
    if (state.sortColumn === column) {
      state.sortDirection = state.sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      state.sortColumn = column;
      state.sortDirection = 'asc';
    }
    renderTable();
  }

  function applyTransform() {
    const column = el('transformColumn').value;
    const type = el('transformType').value;
    
    if (!column) return;
    
    const values = state.rows.map(row => toNumber(row[column])).filter(value => value !== null);
    const needsNumericValues = type !== 'one_hot' && type !== 'label';

    if (needsNumericValues && !values.length) {
      window.alert('Select a column with numeric values before applying this transformation.');
      return;
    }
    
    switch (type) {
      case 'normalize_minmax':
        const min = Math.min(...values);
        const max = Math.max(...values);
        const range = max - min || 1;
        state.rows.forEach(row => {
          const val = toNumber(row[column]);
          row[column] = val !== null ? (val - min) / range : '';
        });
        state.transforms.push({ column, type: 'Min-Max Normalization' });
        break;
      case 'normalize_zscore':
        const meanValue = mean(values);
        const std = Math.sqrt(values.reduce((sum, val) => sum + (val - meanValue) ** 2, 0) / values.length) || 1;
        state.rows.forEach(row => {
          const val = toNumber(row[column]);
          row[column] = val !== null ? (val - meanValue) / std : '';
        });
        state.transforms.push({ column, type: 'Z-Score Standardization' });
        break;
      case 'log':
        state.rows.forEach(row => {
          const val = toNumber(row[column]);
          row[column] = val !== null && val > 0 ? Math.log(val) : '';
        });
        state.transforms.push({ column, type: 'Log Transform' });
        break;
      case 'log10':
        state.rows.forEach(row => {
          const val = toNumber(row[column]);
          row[column] = val !== null && val > 0 ? Math.log10(val) : '';
        });
        state.transforms.push({ column, type: 'Log10 Transform' });
        break;
      case 'sqrt':
        state.rows.forEach(row => {
          const val = toNumber(row[column]);
          row[column] = val !== null && val >= 0 ? Math.sqrt(val) : '';
        });
        state.transforms.push({ column, type: 'Square Root' });
        break;
      case 'one_hot':
        const uniqueValues = [...new Set(state.rows.map(row => row[column]))];
        uniqueValues.forEach(val => {
          const newCol = column + '_' + String(val).replace(/[^a-zA-Z0-9]/g, '_');
          state.columns.push(newCol);
          state.rows.forEach(row => {
            row[newCol] = row[column] === val ? '1' : '0';
          });
        });
        state.transforms.push({ column, type: 'One-Hot Encoding' });
        break;
      case 'label':
        const uniqueLabels = [...new Set(state.rows.map(row => row[column]))];
        const labelMap = {};
        uniqueLabels.forEach((val, idx) => labelMap[val] = idx);
        state.rows.forEach(row => {
          row[column] = labelMap[row[column]];
        });
        state.transforms.push({ column, type: 'Label Encoding' });
        break;
    }
    
    detectNumericColumns();
    renderAll();
    renderTransformHistory();
  }

  function resetTransforms() {
    state.rows = JSON.parse(JSON.stringify(state.originalRows));
    state.transforms = [];
    detectNumericColumns();
    renderAll();
    renderTransformHistory();
  }

  function renderTransformHistory() {
    const container = el('transformHistory');
    container.innerHTML = state.transforms.map((t, i) => 
      '<span class="filter-tag">' + escapeHtml(t.column) + ': ' + escapeHtml(t.type) + '</span>'
    ).join('');
  }

  function renderInsights() {
    const list = el('insightList');
    if (!state.rows.length) {
      list.innerHTML = [
        insight('Dataset needed', 'Upload or load a sample dataset to populate findings.'),
        insight('Supported input', 'CSV, TSV, Excel, and JSON files are available in this frontend version.'),
        insight('Backend status', 'The Django backend exposes health, upload, and analysis endpoints.')
      ].join('');
      return;
    }

    const stats = missingStats();
    const score = qualityScore();
    const topNumeric = state.numericColumns[0];
    const values = topNumeric ? getNumericValues(topNumeric) : [];
    const outliers = topNumeric ? countOutliers(values) : 0;

    list.innerHTML = [
      insight('Dataset loaded', state.rows.length + ' rows and ' + state.columns.length + ' columns are ready.'),
      insight('Numeric coverage', state.numericColumns.length + ' numeric fields detected for analysis.'),
      insight('Data quality', (score ?? 0) + '% readiness with ' + stats.missing + ' missing cells.'),
      insight('Outlier scan', topNumeric ? outliers + ' possible outliers in ' + topNumeric + '.' : 'No numeric column is available yet.')
    ].join('');
  }

  function insight(title, body) {
    return '<li><strong>' + escapeHtml(title) + '</strong><span>' + escapeHtml(body) + '</span></li>';
  }

  function drawChart() {
    const canvas = el('profileChart');
    const context = canvas.getContext('2d');
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.fillStyle = getCss('--surface-soft');
    context.fillRect(0, 0, canvas.width, canvas.height);

    const chartType = el('chartType').value;
    const column = el('chartColumn').value || state.numericColumns[0];
    const column2 = el('chartColumn2').value;

    if (!state.numericColumns.length) {
      drawEmptyChart(context, canvas, 'Load numeric data to draw a profile.');
      return;
    }

    switch (chartType) {
      case 'histogram':
        drawHistogram(context, canvas, column);
        break;
      case 'scatter':
        drawScatterPlot(context, canvas, column, column2);
        break;
      case 'line':
        drawLineChart(context, canvas, column, column2);
        break;
      case 'pie':
        drawPieChart(context, canvas, column);
        break;
      case 'box':
        drawBoxPlot(context, canvas, column);
        break;
    }
  }

  function drawHistogram(context, canvas, column) {
    const values = getNumericValues(column);
    if (!values.length) {
      drawEmptyChart(context, canvas, 'Load numeric data to draw a profile.');
      return;
    }

    const padding = { left: 64, right: 28, top: 28, bottom: 54 };
    const min = Math.min(...values);
    const max = Math.max(...values);
    const bins = Math.min(10, Math.max(4, Math.ceil(Math.sqrt(values.length))));
    const width = canvas.width - padding.left - padding.right;
    const height = canvas.height - padding.top - padding.bottom;
    const binSize = max === min ? 1 : (max - min) / bins;
    const counts = Array.from({ length: bins }, () => 0);

    values.forEach((value) => {
      const index = max === min ? 0 : Math.min(bins - 1, Math.floor((value - min) / binSize));
      counts[index] += 1;
    });

    const maxCount = Math.max(...counts, 1);
    context.strokeStyle = getCss('--line');
    context.lineWidth = 2;
    context.beginPath();
    context.moveTo(padding.left, padding.top);
    context.lineTo(padding.left, padding.top + height);
    context.lineTo(padding.left + width, padding.top + height);
    context.stroke();

    counts.forEach((count, index) => {
      const barWidth = width / bins - 12;
      const x = padding.left + index * (width / bins) + 6;
      const barHeight = (count / maxCount) * (height - 20);
      const y = padding.top + height - barHeight;
      context.fillStyle = index % 2 === 0 ? getCss('--accent') : getCss('--green');
      context.fillRect(x, y, barWidth, barHeight);
    });

    context.fillStyle = getCss('--muted');
    context.font = '14px sans-serif';
    context.fillText(String(round(min)), padding.left, canvas.height - 22);
    context.fillText(String(round(max)), canvas.width - padding.right - 60, canvas.height - 22);
    context.fillStyle = getCss('--text');
    context.font = '700 16px sans-serif';
    context.fillText(column, padding.left, 22);
  }

  function drawScatterPlot(context, canvas, columnX, columnY) {
    const xValues = getNumericValues(columnX);
    const yValues = columnY ? getNumericValues(columnY) : xValues;

    if (!xValues.length || !yValues.length) {
      drawEmptyChart(context, canvas, 'Need numeric data for scatter plot.');
      return;
    }

    const padding = { left: 64, right: 28, top: 28, bottom: 54 };
    const width = canvas.width - padding.left - padding.right;
    const height = canvas.height - padding.top - padding.bottom;

    const minX = Math.min(...xValues);
    const maxX = Math.max(...xValues);
    const minY = Math.min(...yValues);
    const maxY = Math.max(...yValues);

    const rangeX = maxX - minX || 1;
    const rangeY = maxY - minY || 1;

    context.strokeStyle = getCss('--line');
    context.lineWidth = 2;
    context.beginPath();
    context.moveTo(padding.left, padding.top);
    context.lineTo(padding.left, padding.top + height);
    context.lineTo(padding.left + width, padding.top + height);
    context.stroke();

    const pairs = Math.min(xValues.length, yValues.length);
    for (let i = 0; i < pairs; i++) {
      const x = padding.left + ((xValues[i] - minX) / rangeX) * width;
      const y = padding.top + height - ((yValues[i] - minY) / rangeY) * height;
      context.fillStyle = getCss('--accent');
      context.beginPath();
      context.arc(x, y, 5, 0, Math.PI * 2);
      context.fill();
    }

    context.fillStyle = getCss('--muted');
    context.font = '14px sans-serif';
    context.fillText(String(round(minX)), padding.left, canvas.height - 22);
    context.fillText(String(round(maxX)), canvas.width - padding.right - 60, canvas.height - 22);
    context.fillText(String(round(minY)), padding.left - 50, canvas.height - 22);
    context.fillText(String(round(maxY)), padding.left - 50, padding.top + 20);
    context.fillStyle = getCss('--text');
    context.font = '700 16px sans-serif';
    context.fillText(columnX + (columnY ? ' vs ' + columnY : ''), padding.left, 22);
  }

  function drawLineChart(context, canvas, columnX, columnY) {
    const xValues = getNumericValues(columnX);
    const yValues = columnY ? getNumericValues(columnY) : xValues;

    if (!xValues.length || !yValues.length) {
      drawEmptyChart(context, canvas, 'Need numeric data for line chart.');
      return;
    }

    const padding = { left: 64, right: 28, top: 28, bottom: 54 };
    const width = canvas.width - padding.left - padding.right;
    const height = canvas.height - padding.top - padding.bottom;

    const minX = Math.min(...xValues);
    const maxX = Math.max(...xValues);
    const minY = Math.min(...yValues);
    const maxY = Math.max(...yValues);

    const rangeX = maxX - minX || 1;
    const rangeY = maxY - minY || 1;

    context.strokeStyle = getCss('--line');
    context.lineWidth = 2;
    context.beginPath();
    context.moveTo(padding.left, padding.top);
    context.lineTo(padding.left, padding.top + height);
    context.lineTo(padding.left + width, padding.top + height);
    context.stroke();

    const pairs = Math.min(xValues.length, yValues.length);
    const sortedIndices = Array.from({ length: pairs }, (_, i) => i)
      .sort((a, b) => xValues[a] - xValues[b]);

    context.strokeStyle = getCss('--accent');
    context.lineWidth = 3;
    context.beginPath();

    sortedIndices.forEach((i, index) => {
      const x = padding.left + ((xValues[i] - minX) / rangeX) * width;
      const y = padding.top + height - ((yValues[i] - minY) / rangeY) * height;
      if (index === 0) {
        context.moveTo(x, y);
      } else {
        context.lineTo(x, y);
      }
    });
    context.stroke();

    sortedIndices.forEach((i) => {
      const x = padding.left + ((xValues[i] - minX) / rangeX) * width;
      const y = padding.top + height - ((yValues[i] - minY) / rangeY) * height;
      context.fillStyle = getCss('--green');
      context.beginPath();
      context.arc(x, y, 4, 0, Math.PI * 2);
      context.fill();
    });

    context.fillStyle = getCss('--muted');
    context.font = '14px sans-serif';
    context.fillText(String(round(minX)), padding.left, canvas.height - 22);
    context.fillText(String(round(maxX)), canvas.width - padding.right - 60, canvas.height - 22);
    context.fillText(String(round(minY)), padding.left - 50, canvas.height - 22);
    context.fillText(String(round(maxY)), padding.left - 50, padding.top + 20);
    context.fillStyle = getCss('--text');
    context.font = '700 16px sans-serif';
    context.fillText(columnX + (columnY ? ' vs ' + columnY : ''), padding.left, 22);
  }

  function drawPieChart(context, canvas, column) {
    const values = getNumericValues(column);
    if (!values.length) {
      drawEmptyChart(context, canvas, 'Need numeric data for pie chart.');
      return;
    }

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = Math.min(centerX, centerY) - 40;

    const bins = 5;
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;
    const binSize = range / bins;
    const counts = Array.from({ length: bins }, () => 0);

    values.forEach((value) => {
      const index = Math.min(bins - 1, Math.floor((value - min) / binSize));
      counts[index] += 1;
    });

    const total = counts.reduce((sum, count) => sum + count, 0);
    const colors = [getCss('--accent'), getCss('--green'), getCss('--amber'), getCss('--red'), getCss('--muted')];

    let startAngle = -Math.PI / 2;
    counts.forEach((count, index) => {
      if (count === 0) return;
      const sliceAngle = (count / total) * Math.PI * 2;
      context.fillStyle = colors[index];
      context.beginPath();
      context.moveTo(centerX, centerY);
      context.arc(centerX, centerY, radius, startAngle, startAngle + sliceAngle);
      context.closePath();
      context.fill();
      startAngle += sliceAngle;
    });

    context.fillStyle = getCss('--text');
    context.font = '700 16px sans-serif';
    context.textAlign = 'center';
    context.fillText(column, centerX, 30);
    context.textAlign = 'left';
  }

  function drawBoxPlot(context, canvas, column) {
    const values = getNumericValues(column).sort((a, b) => a - b);
    if (values.length < 4) {
      drawEmptyChart(context, canvas, 'Need at least 4 data points for box plot.');
      return;
    }

    const padding = { left: 64, right: 28, top: 28, bottom: 54 };
    const width = canvas.width - padding.left - padding.right;
    const height = canvas.height - padding.top - padding.bottom;

    const q1 = values[Math.floor(values.length * 0.25)];
    const q3 = values[Math.floor(values.length * 0.75)];
    const median = values[Math.floor(values.length * 0.5)];
    const iqr = q3 - q1;
    const min = Math.max(values[0], q1 - 1.5 * iqr);
    const max = Math.min(values[values.length - 1], q3 + 1.5 * iqr);
    const range = max - min || 1;

    const boxX = padding.left + width / 2 - 40;
    const boxWidth = 80;

    context.strokeStyle = getCss('--line');
    context.lineWidth = 2;
    context.beginPath();
    context.moveTo(padding.left, padding.top);
    context.lineTo(padding.left, padding.top + height);
    context.lineTo(padding.left + width, padding.top + height);
    context.stroke();

    const y = (value) => padding.top + height - ((value - min) / range) * height;

    context.strokeStyle = getCss('--accent');
    context.lineWidth = 2;
    context.beginPath();
    context.moveTo(boxX + boxWidth / 2, y(min));
    context.lineTo(boxX + boxWidth / 2, y(q1));
    context.stroke();

    context.fillStyle = getCss('--surface-soft');
    context.strokeStyle = getCss('--accent');
    context.lineWidth = 2;
    context.fillRect(boxX, y(q3), boxWidth, y(q1) - y(q3));
    context.strokeRect(boxX, y(q3), boxWidth, y(q1) - y(q3));

    context.strokeStyle = getCss('--accent');
    context.lineWidth = 2;
    context.beginPath();
    context.moveTo(boxX + boxWidth / 2, y(q3));
    context.lineTo(boxX + boxWidth / 2, y(max));
    context.stroke();

    context.strokeStyle = getCss('--green');
    context.lineWidth = 3;
    context.beginPath();
    context.moveTo(boxX, y(median));
    context.lineTo(boxX + boxWidth, y(median));
    context.stroke();

    context.fillStyle = getCss('--muted');
    context.font = '14px sans-serif';
    context.fillText(String(round(min)), padding.left, canvas.height - 22);
    context.fillText(String(round(max)), canvas.width - padding.right - 60, canvas.height - 22);
    context.fillStyle = getCss('--text');
    context.font = '700 16px sans-serif';
    context.fillText(column, padding.left, 22);
  }

  function drawEmptyChart(context, canvas, message) {
    context.fillStyle = getCss('--muted');
    context.font = '700 18px sans-serif';
    context.textAlign = 'center';
    context.fillText(message, canvas.width / 2, canvas.height / 2);
    context.textAlign = 'left';
  }

  function getCss(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  async function runAnalysis() {
    if (!state.rows.length) {
      state.lastResults = [{ title: 'No dataset', body: 'Load a dataset before running analysis.' }];
      renderResults('Needs data');
      return;
    }

    const type = el('analysisType').value;
    const target = el('targetColumn').value || state.numericColumns[0] || state.columns[0];
    const confidence = Number(el('confidenceRange').value) / 100;

    state.lastResults = [{ title: 'Running analysis', body: 'Please wait while the backend processes the request.', meta: '' }];
    renderResults('Running');

    try {
      const response = await fetch(state.apiBaseUrl + '/datasets/analyze/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          data: {
            columns: state.columns,
            rows: state.rows
          },
          analysis_type: type,
          target,
          confidence
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.message || response.statusText || 'Analysis request failed');
      }

      const data = await response.json();
      state.lastResults = Array.isArray(data.results) ? data.results : [{ title: 'Analysis returned no results', body: 'No results were returned from the backend.', meta: '' }];
    } catch (error) {
      console.error('Backend analysis failed:', error);
      state.lastResults = [{ title: 'Analysis failed', body: error.message || 'Unable to complete analysis.', meta: '' }];
    }

    state.analysisHistory.push({
      type,
      target,
      confidence,
      timestamp: new Date().toISOString(),
      resultCount: state.lastResults.length
    });

    renderResults(state.lastResults.length ? 'Complete' : 'Failed');
    renderReport();
  }

  function descriptiveResults(target) {
    return state.numericColumns.slice(0, 6).map((column) => {
      const values = getNumericValues(column).sort((a, b) => a - b);
      const freq = frequencyDistribution(values);
      return {
        title: column,
        body:
          'Count ' + values.length + ', sum ' + round(sum(values)) + ', mean ' + round(mean(values)) + ', median ' + round(median(values)) + ', mode ' + round(mode(values)) + ', min ' + round(values[0]) + ', max ' + round(values[values.length - 1]) + ', range ' + round(values[values.length - 1] - values[0]) + ', variance ' + round(variance(values)) + ', std dev ' + round(stdDev(values)) + ', std error ' + round(stdError(values)) + ', Q1 ' + round(percentile(values, 25)) + ', Q2 ' + round(percentile(values, 50)) + ', Q3 ' + round(percentile(values, 75)) + ', IQR ' + round(iqr(values)) + ', skew ' + round(skewness(values)) + ', kurtosis ' + round(kurtosis(values)),
        meta: 'First 6 numeric columns'
      };
    });
  }

  function inferentialResults(target, confidence) {
    const values = getNumericValues(target);
    if (!values.length) return [{ title: 'No numeric data', body: 'Select a numeric target column for inferential statistics.', meta: '' }];
    const sample = values.slice(0, Math.min(values.length, 50));
    const meanValue = mean(sample);
    const sem = stdError(sample);
    const margin = sem * 1.96;
    return [
      { title: 'Confidence interval', body: round(meanValue - margin) + ' to ' + round(meanValue + margin), meta: confidence + '% approx.' },
      { title: 'Margin of error', body: round(margin), meta: 'Based on sample size ' + sample.length },
      { title: 'Population estimation', body: 'Estimated mean ' + round(meanValue), meta: 'Using sample values' },
      { title: 'Sampling distribution', body: 'Central limit approximation for samples of size ' + sample.length, meta: 'Normality assumed' }
    ];
  }

  function correlationResults(target) {
    const targetValues = state.rows.map((row) => toNumber(row[target]));
    return state.numericColumns.filter((column) => column !== target).slice(0, 6).map((column) => {
      const pairs = [];
      state.rows.forEach((row, index) => {
        const x = toNumber(row[column]);
        const y = targetValues[index];
        if (x !== null && y !== null) pairs.push([x, y]);
      });
      const r = pearson(pairs);
      const strength = Math.abs(r) >= 0.7 ? 'strong' : Math.abs(r) >= 0.4 ? 'moderate' : 'weak';
      return {
        title: column + ' vs ' + target,
        body: 'Pearson correlation ' + round(r) + ' (' + strength + ').',
        meta: pairs.length + ' matched pairs'
      };
    });
  }

  function regressionAnalysisResults(target, confidence) {
    const numericFeatures = state.numericColumns.filter((col) => col !== target);
    const featureCount = numericFeatures.length;
    const usableRows = state.rows.filter((row) => numericFeatures.every((col) => toNumber(row[col]) !== null) && toNumber(row[target]) !== null).length;
    return [
      { title: 'Target variable', body: target || 'None selected', meta: 'Regression analysis' },
      { title: 'Available predictors', body: featureCount + ' numeric features', meta: numericFeatures.join(', ') || 'None' },
      { title: 'Usable rows', body: usableRows, meta: 'After filtering missing values' },
      { title: 'Model recommendation', body: featureCount === 1 ? 'Simple linear regression' : 'Multiple linear regression', meta: 'Confidence ' + confidence + '%' },
      { title: 'Diagnostics', body: 'R-squared estimation available after model training', meta: 'Placeholder summary' }
    ];
  }

  function hypothesisResults(target, confidence) {
    const values = getNumericValues(target);
    if (values.length < 2) return [{ title: 'Insufficient data', body: 'Need at least 2 numeric values for hypothesis tests.', meta: 'Error' }];
    return [
      { title: 'One sample t-test', body: 'Mean = ' + round(mean(values)) + ', t-statistic approx. ' + round(mean(values) / stdError(values)), meta: 'Against null mean 0' },
      { title: 'Paired t-test', body: 'Requires paired data; use related dataset pairs for best results.', meta: 'Not computed' },
      { title: 'ANOVA summary', body: state.numericColumns.length >= 3 ? 'Multiple group variance analysis ready.' : 'Need at least 3 numeric variables.', meta: 'Use ANOVA panel for details' },
      { title: 'Chi-square test', body: 'Categorical frequency test available when category counts exist.', meta: 'Requires nonnumeric categorical data' }
    ];
  }

  function timeSeriesResults(target) {
    const values = getNumericValues(target);
    if (values.length < 3) return [{ title: 'Insufficient data', body: 'Need at least 3 values for time series analysis.', meta: 'Error' }];
    return [
      { title: 'Trend analysis', body: 'Sequential trend line can be approximated from target values.', meta: 'Linear trend expected' },
      { title: 'Moving average', body: '3-point moving average is available for smoothing.', meta: 'Simple smoothing' },
      { title: 'Seasonal decomposition', body: 'Seasonality detection requires repeated cycles in data.', meta: 'Use regular intervals' },
      { title: 'Forecasting', body: 'Naive forecast for next point: ' + round(values[values.length - 1]), meta: 'One-step ahead' },
      { title: 'ARIMA model', body: 'ARIMA modeling is available in backend extension modules.', meta: 'Not computed in frontend' }
    ];
  }

  function distributionResults(target) {
    const values = getNumericValues(target);
    if (!values.length) return [{ title: 'No numeric data', body: 'Select a numeric column to analyze distributions.', meta: '' }];
    return [
      { title: 'Normal distribution', body: 'Mean ' + round(mean(values)) + ', std dev ' + round(stdDev(values)), meta: 'Approximate normality' },
      { title: 'Histogram', body: 'Histogram bins available in visualization panel.', meta: 'Visual distribution' },
      { title: 'Density plot', body: 'Kernel density is approximated by value frequency.', meta: 'Smooth estimate' },
      { title: 'Q-Q plot', body: 'Quantile comparison with normal distribution can be generated.', meta: 'Goodness-of-fit hint' }
    ];
  }

  function dataQualityResults() {
    const stats = missingStats();
    return [
      { title: 'Missing values', body: stats.missing + ' missing cells', meta: 'Rate ' + Math.round(stats.rate * 100) + '%' },
      { title: 'Duplicate records', body: countDuplicates() + ' duplicate rows', meta: 'Current scan' },
      { title: 'Outlier detection', body: countTotalOutliers() + ' outliers found', meta: 'IQR-based' },
      { title: 'Consistency check', body: calculateTypeConsistency() + '% consistent columns', meta: 'Type uniformity' },
      { title: 'Completeness', body: calculateCompleteness() + '% complete data', meta: 'Non-empty cells' }
    ];
  }

  function aiRecommendationResults() {
    const recommendation = recommendAnalysisType();
    const visualization = recommendVisualization();
    const cleaning = recommendCleaningSteps();
    return [
      { title: 'Recommended statistical test', body: recommendation.test, meta: recommendation.reason },
      { title: 'Recommended visualization', body: visualization, meta: 'Based on data types' },
      { title: 'Cleaning recommendation', body: cleaning, meta: 'Data quality advice' },
      { title: 'Plain English summary', body: 'The dataset is best analyzed with the recommended test working on numeric and categorical columns.', meta: 'AI-guided recommendation' }
    ];
  }

  function classificationResults(target) {
    const classes = [...new Set(state.rows.map((row) => row[target]))].filter((value) => value !== '' && value !== null);
    return [
      { title: 'Classification scenario', body: classes.length <= 10 ? 'Suitable for decision tree or random forest classification.' : 'Large cardinality categorical target may require encoding.', meta: target },
      { title: 'Recommended classifiers', body: 'Decision Tree, Random Forest, SVM, KNN, Logistic Regression', meta: 'Standard classification models' }
    ];
  }

  function mlRegressionResults(target) {
    return [
      { title: 'Regression modeling', body: 'Use numeric target with multiple predictors for regression.', meta: target },
      { title: 'Recommended algorithms', body: 'Linear Regression, Ridge, Lasso', meta: 'Good for numeric prediction' },
      { title: 'Performance note', body: 'Use cross-validation and feature importance to assess models.', meta: 'Model validation' }
    ];
  }

  function clusteringResults(target) {
    const numericCount = state.numericColumns.length;
    return [
      { title: 'Clustering readiness', body: numericCount >= 2 ? 'Data ready for K-Means, DBSCAN, or Hierarchical Clustering.' : 'Add more numeric features for clustering.', meta: numericCount + ' numeric fields' },
      { title: 'Suggested clustering', body: 'K-Means for compact clusters, DBSCAN for density-based anomalies, Hierarchical for tree structure.', meta: 'Clustering module' }
    ];
  }

  function modelEvaluationResults() {
    return [
      { title: 'Model evaluation metrics', body: 'Use accuracy, precision, recall, F1 score for classification and RMSE/MAPE for regression.', meta: 'Standard metrics' },
      { title: 'Feature importance', body: 'Calculate importance using correlation, variance, or tree-based scores.', meta: 'Model explainability' }
    ];
  }

  function frequencyDistribution(values) {
    const map = {};
    values.forEach((value) => { map[value] = (map[value] || 0) + 1; });
    return Object.entries(map).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([value, count]) => value + ': ' + count);
  }

  function recommendAnalysisType() {
    const categoricalColumns = state.columns.filter((column) => !state.numericColumns.includes(column));
    if (state.numericColumns.length === 1 && categoricalColumns.length === 1) {
      return { test: 'Independent T-Test', reason: 'One numeric and one categorical variable detected.' };
    }
    if (state.numericColumns.length >= 2) {
      return { test: 'Multiple Linear Regression', reason: 'Multiple numeric predictors are available.' };
    }
    if (categoricalColumns.length >= 1) {
      return { test: 'Chi-Square Test', reason: 'Categorical frequencies are available.' };
    }
    return { test: 'Descriptive Statistics', reason: 'Describe the current dataset first.' };
  }

  function recommendVisualization() {
    if (state.numericColumns.length >= 2) return 'Scatter plot or line chart for numeric relationships.';
    if (state.numericColumns.length === 1) return 'Histogram or box plot for numeric distribution.';
    return 'Bar chart for categorical counts.';
  }

  function recommendCleaningSteps() {
    const stats = missingStats();
    if (stats.rate > 0.2) return 'Impute or drop missing values before modeling.';
    if (countDuplicates() > 0) return 'Remove duplicate records to improve analysis quality.';
    return 'Dataset is reasonably clean; validate data types and outliers.';
  }

  function regressionDiagnostics(values, targetValues) {
    const slope = 0;
    return { slope, intercept: 0, rSquared: 0 };
  }

  function handleOutliers() {
    const results = [];
    state.numericColumns.forEach(column => {
      const values = getNumericValues(column);
      if (values.length < 4) return;
      
      const sorted = [...values].sort((a, b) => a - b);
      const q1 = sorted[Math.floor(sorted.length * 0.25)];
      const q3 = sorted[Math.floor(sorted.length * 0.75)];
      const iqr = q3 - q1;
      const low = q1 - 1.5 * iqr;
      const high = q3 + 1.5 * iqr;
      
      const outliers = values.filter(v => v < low || v > high);
      if (outliers.length > 0) {
        results.push({
          title: column,
          body: outliers.length + ' outliers detected. Range: ' + round(low) + ' to ' + round(high),
          meta: 'IQR method'
        });
      }
    });
    
    if (results.length === 0) {
      results.push({ title: 'No outliers', body: 'No significant outliers detected in numeric columns.', meta: 'IQR method' });
    }
    
    state.lastResults = results;
    renderResults('Complete');
    renderReport();
  }

  function renderResults(status) {
    const statusEl = el('runStatus');
    statusEl.textContent = status;
    statusEl.classList.toggle('ready', status === 'Complete');
    const results = state.lastResults;
    el('analysisResults').innerHTML = results.length ? results.map((item) => {
      return '<article class="result-item"><strong>' + escapeHtml(item.title) + '</strong><span>' + escapeHtml(item.body) + '</span><small>' + escapeHtml(item.meta || '') + '</small></article>';
    }).join('') : '<div class="empty-state">Run an analysis to view results.</div>';
    
    renderAnalysisHistory();
  }

  function renderAnalysisHistory() {
    const container = el('analysisHistory');
    if (state.analysisHistory.length === 0) {
      container.innerHTML = '<div class="empty-state">No analysis history yet.</div>';
      return;
    }
    
    container.innerHTML = state.analysisHistory.slice(-10).reverse().map((item) => {
      const date = new Date(item.timestamp);
      return '<div class="history-item"><strong>' + escapeHtml(item.type) + '</strong><span>' + escapeHtml(item.target || 'N/A') + '</span><small>' + date.toLocaleTimeString() + '</small></div>';
    }).join('');
  }

  function clearHistory() {
    state.analysisHistory = [];
    renderAnalysisHistory();
  }

  function renderReport() {
    el('reportDate').textContent = new Date().toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
    const rows = [
      { title: 'Dataset', body: state.name ? state.name + ' with ' + state.rows.length + ' rows and ' + state.columns.length + ' columns.' : 'No dataset loaded.' },
      { title: 'Data quality', body: qualityScore() === null ? 'No score available.' : qualityScore() + '% readiness score.' },
      { title: 'Numeric fields', body: state.numericColumns.length ? state.numericColumns.join(', ') : 'No numeric fields detected.' }
    ].concat(state.lastResults.map((result) => ({ title: result.title, body: result.body })));

    el('reportBody').innerHTML = rows.map((row) => {
      return '<article class="report-section"><h4>' + escapeHtml(row.title) + '</h4><p>' + escapeHtml(row.body) + '</p></article>';
    }).join('');
  }

  function renderAll() {
    renderMetrics();
    renderSelects();
    renderTable();
    renderInsights();
    updateHeroPanel();
    renderAiRecommendations();
    renderResults(state.lastResults.length ? 'Complete' : 'Idle');
    renderReport();
    requestAnimationFrame(drawChart);
  }

  function setView(viewId) {
    state.activeView = viewId;
    document.querySelectorAll('.view').forEach((view) => view.classList.toggle('active', view.id === viewId));
    document.querySelectorAll('.nav-item').forEach((button) => button.classList.toggle('active', button.dataset.view === viewId));
    if (viewId === 'dashboard') requestAnimationFrame(drawChart);
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[char]));
  }

  function round(value) {
    if (!Number.isFinite(value)) return 0;
    return Math.round(value * 100) / 100;
  }

  function mean(values) {
    return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0;
  }

  function median(values) {
    if (!values.length) return 0;
    const middle = Math.floor(values.length / 2);
    return values.length % 2 ? values[middle] : (values[middle - 1] + values[middle]) / 2;
  }

  function sum(values) {
    return values.reduce((total, value) => total + value, 0);
  }

  function variance(values, sample = false) {
    if (!values.length) return 0;
    const meanValue = mean(values);
    const squared = values.reduce((total, value) => total + (value - meanValue) ** 2, 0);
    return squared / (values.length - (sample ? 1 : 0) || 1);
  }

  function stdDev(values, sample = false) {
    return Math.sqrt(variance(values, sample));
  }

  function stdError(values) {
    return values.length ? stdDev(values, true) / Math.sqrt(values.length) : 0;
  }

  function percentile(values, percent) {
    if (!values.length) return 0;
    const index = (values.length - 1) * (percent / 100);
    const lower = Math.floor(index);
    const upper = Math.ceil(index);
    const weight = index - lower;
    return upper >= values.length ? values[lower] : values[lower] * (1 - weight) + values[upper] * weight;
  }

  function iqr(values) {
    return percentile(values, 75) - percentile(values, 25);
  }

  function skewness(values) {
    if (!values.length) return 0;
    const meanValue = mean(values);
    const sd = stdDev(values);
    if (sd === 0) return 0;
    return values.reduce((sumValue, value) => sumValue + ((value - meanValue) / sd) ** 3, 0) / values.length;
  }

  function kurtosis(values) {
    if (!values.length) return 0;
    const meanValue = mean(values);
    const sd = stdDev(values);
    if (sd === 0) return 0;
    return values.reduce((sumValue, value) => sumValue + ((value - meanValue) / sd) ** 4, 0) / values.length - 3;
  }

  function mode(values) {
    if (!values.length) return 0;
    const counts = {};
    values.forEach((value) => { counts[value] = (counts[value] || 0) + 1; });
    return Number(Object.keys(counts).reduce((maxKey, key) => counts[key] > counts[maxKey] ? key : maxKey, Object.keys(counts)[0]));
  }

  function pearson(pairs) {
    if (pairs.length < 2) return 0;
    const xs = pairs.map((pair) => pair[0]);
    const ys = pairs.map((pair) => pair[1]);
    const mx = mean(xs);
    const my = mean(ys);
    let numerator = 0;
    let dx = 0;
    let dy = 0;
    pairs.forEach(([x, y]) => {
      numerator += (x - mx) * (y - my);
      dx += (x - mx) ** 2;
      dy += (y - my) ** 2;
    });
    const denominator = Math.sqrt(dx * dy);
    return denominator ? numerator / denominator : 0;
  }

  function countOutliers(values) {
    if (values.length < 4) return 0;
    const sorted = [...values].sort((a, b) => a - b);
    const q1 = sorted[Math.floor(sorted.length * 0.25)];
    const q3 = sorted[Math.floor(sorted.length * 0.75)];
    const iqr = q3 - q1;
    const low = q1 - 1.5 * iqr;
    const high = q3 + 1.5 * iqr;
    return values.filter((value) => value < low || value > high).length;
  }

  function countDuplicates() {
    if (!state.rows.length) return 0;
    const seen = new Set();
    let duplicates = 0;
    state.rows.forEach(row => {
      const key = JSON.stringify(row);
      if (seen.has(key)) {
        duplicates++;
      } else {
        seen.add(key);
      }
    });
    return duplicates;
  }

  function countTotalOutliers() {
    let total = 0;
    state.numericColumns.forEach(column => {
      const values = getNumericValues(column);
      if (values.length >= 4) {
        total += countOutliers(values);
      }
    });
    return total;
  }

  function calculateTypeConsistency() {
    if (!state.columns.length) return 0;
    let consistentColumns = 0;
    state.columns.forEach(column => {
      const types = new Set();
      state.rows.forEach(row => {
        const val = row[column];
        if (val === null || val === undefined || val === '') return;
        if (isNumericValue(val)) types.add('numeric');
        else types.add('string');
      });
      if (types.size <= 1) consistentColumns++;
    });
    return Math.round((consistentColumns / state.columns.length) * 100);
  }

  function calculateCompleteness() {
    if (!state.columns.length || !state.rows.length) return 0;
    const stats = missingStats();
    return Math.round((1 - stats.rate) * 100);
  }

  function download(filename, content, type) {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  function buildCsv() {
    if (!state.columns.length) return '';
    const quote = (value) => '"' + String(value ?? '').replace(/"/g, '""') + '"';
    const lines = [state.columns.map(quote).join(',')];
    state.rows.forEach((row) => lines.push(state.columns.map((column) => quote(row[column])).join(',')));
    return lines.join('\n');
  }

  function buildReportText() {
    const lines = [
      'AI-Based Statistical Analysis System',
      'Report date: ' + new Date().toLocaleString(),
      '',
      'Dataset: ' + (state.name || 'No dataset loaded'),
      'Rows: ' + state.rows.length,
      'Columns: ' + state.columns.length,
      'Readiness: ' + (qualityScore() === null ? 'N/A' : qualityScore() + '%'),
      '',
      'Results:'
    ];
    if (!state.lastResults.length) lines.push('No analysis has been run.');
    state.lastResults.forEach((result) => lines.push('- ' + result.title + ': ' + result.body));
    return lines.join('\n');
  }

  function buildReportJson() {
    return JSON.stringify({
      system: 'AI-Based Statistical Analysis System',
      reportDate: new Date().toISOString(),
      dataset: {
        name: state.name || 'No dataset loaded',
        rows: state.rows.length,
        columns: state.columns.length,
        readiness: qualityScore()
      },
      metrics: {
        qualityScore: qualityScore(),
        missingRate: missingStats().rate,
        numericColumns: state.numericColumns.length
      },
      results: state.lastResults,
      history: state.analysisHistory
    }, null, 2);
  }

  function buildReportWord() {
    const rows = [
      { title: 'Dataset', body: state.name ? state.name + ' (' + state.rows.length + ' rows, ' + state.columns.length + ' columns)' : 'No dataset loaded.' },
      { title: 'Quality score', body: qualityScore() === null ? 'N/A' : qualityScore() + '%' },
      { title: 'Numeric fields', body: state.numericColumns.length ? state.numericColumns.join(', ') : 'None' }
    ].concat(state.lastResults.map((result) => ({ title: result.title, body: result.body })));

    const html = ['<html><head><meta charset="UTF-8"><title>Statistical Report</title></head><body>'];
    html.push('<h1>AI-Based Statistical Analysis System</h1>');
    html.push('<p>Report date: ' + new Date().toLocaleString() + '</p>');
    rows.forEach((row) => {
      html.push('<h2>' + escapeHtml(row.title) + '</h2>');
      html.push('<p>' + escapeHtml(row.body) + '</p>');
    });
    html.push('</body></html>');
    return html.join('');
  }

  function exportReport() {
    const format = el('exportFormat').value;
    if (format === 'json') {
      download('analysis-report.json', buildReportJson(), 'application/json');
      return;
    }

    if (format === 'csv') {
      download((state.name || 'dataset').replace(/\.csv$/i, '') + '-export.csv', buildCsv(), 'text/csv');
      return;
    }

    if (format === 'excel') {
      downloadExcelReport();
      return;
    }

    if (format === 'pdf') {
      const doc = new window.jspdf.jsPDF();
      const lines = buildReportText().split('\n');
      let y = 20;
      doc.setFontSize(12);
      lines.forEach((line) => {
        if (y > 270) {
          doc.addPage();
          y = 20;
        }
        doc.text(line, 14, y);
        y += 8;
      });
      doc.save('analysis-report.pdf');
      return;
    }

    if (format === 'word') {
      download('analysis-report.doc', buildReportWord(), 'application/msword');
      return;
    }

    download('analysis-report.txt', buildReportText(), 'text/plain');
  }

  function downloadExcelReport() {
    const data = [state.columns].concat(state.rows.map((row) => state.columns.map((column) => row[column] ?? '')));
    const worksheet = XLSX.utils.aoa_to_sheet(data);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Report');
    const workbookArray = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
    const blob = new Blob([workbookArray], { type: 'application/octet-stream' });
    const filename = (state.name || 'dataset').replace(/\.csv$/i, '') + '-report.xlsx';
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  function saveSession() {
    if (!state.rows.length) {
      window.alert('No data to save. Load a dataset first.');
      return;
    }
    
    const session = {
      name: state.name,
      columns: state.columns,
      rows: state.rows,
      originalRows: state.originalRows,
      numericColumns: state.numericColumns,
      transforms: state.transforms,
      lastResults: state.lastResults,
      savedAt: new Date().toISOString()
    };
    
    localStorage.setItem('ai-stats-session', JSON.stringify(session));
    window.alert('Session saved successfully!');
  }

  function loadSession() {
    const saved = localStorage.getItem('ai-stats-session');
    if (!saved) {
      window.alert('No saved session found.');
      return;
    }
    
    try {
      const session = JSON.parse(saved);
      state.name = session.name;
      state.columns = session.columns;
      state.rows = session.rows;
      state.originalRows = session.originalRows;
      state.numericColumns = session.numericColumns;
      state.transforms = session.transforms || [];
      state.lastResults = session.lastResults || [];
      state.filteredRows = state.rows;
      state.filters = [];
      state.sortColumn = null;
      state.sortDirection = 'asc';
      
      renderAll();
      renderTransformHistory();
      window.alert('Session loaded successfully! Saved: ' + new Date(session.savedAt).toLocaleString());
    } catch (e) {
      window.alert('Error loading session: ' + e.message);
    }
  }

  async function checkBackendHealth() {
    try {
      const response = await fetch(state.apiBaseUrl + '/health/');
      if (response.ok) {
        const data = await response.json();
        console.log('Backend health:', data);
        return true;
      }
      return false;
    } catch (e) {
      console.log('Backend not available:', e.message);
      return false;
    }
  }

  async function uploadToBackend() {
    if (!state.rows.length) {
      window.alert('No data to upload. Load a dataset first.');
      return;
    }

    try {
      const response = await fetch(state.apiBaseUrl + '/datasets/upload/', {
        method: 'POST',
        body: createDatasetFormData(),
      });
      
      if (response.ok) {
        const data = await response.json();
        window.alert('Dataset uploaded successfully! File: ' + data.filename);
      } else {
        const errorData = await response.json().catch(() => null);
        window.alert('Upload failed: ' + (errorData?.message || response.statusText));
      }
    } catch (e) {
      window.alert('Error uploading to backend: ' + e.message);
    }
  }

  function createDatasetFormData() {
    const formData = new FormData();
    formData.append('dataset', new Blob([buildCsv()], { type: 'text/csv' }), state.name || 'dataset.csv');
    return formData;
  }

  function loadCsvText(name, text) {
    const parsed = parseCsv(text);
    if (!parsed.columns.length) {
      window.alert('No rows were found in that CSV file.');
      return;
    }
    setDataset(name, parsed.columns, parsed.rows);
  }

  function handleQuickAnalysis() {
    if (!state.rows.length) {
      showToast('Load a dataset before running guided analysis.', 'warning');
      setView('datasets');
      return;
    }

    const topNumeric = state.numericColumns[0];
    if (!topNumeric) {
      showToast('Add at least one numeric column to run guided analysis.', 'warning');
      return;
    }

    const values = getNumericValues(topNumeric);
    const outliers = countOutliers(values);
    state.lastResults = [
      ...state.lastResults,
      {
        title: 'Guided analysis',
        body: `${topNumeric} shows ${outliers} possible outliers across ${state.rows.length} records.`
      }
    ];

    renderAll();
    showToast('Guided analysis generated successfully.', 'success');
  }

  function renderAiRecommendations() {
    const list = el('aiRecommendationList');
    const explanation = el('aiInsights');

    if (!list || !explanation) return;

    if (!state.rows.length) {
      list.innerHTML = '<div class="ai-recommendation-card"><strong>Upload a dataset first</strong><span>Once data is loaded, the assistant will suggest the best statistical methods and modeling approach.</span></div>';
      explanation.innerHTML = '<li class="insight-list li"><strong>Waiting for data</strong><span>Bring in a dataset to unlock AI-driven analysis recommendations.</span></li>';
      return;
    }

    const recommendations = [];
    if (state.numericColumns.length >= 2) {
      recommendations.push({ title: 'Correlation analysis', body: 'Strong numeric structure detected. Explore pairwise relationships and dependencies.' });
    }
    if (state.numericColumns.length >= 1) {
      recommendations.push({ title: 'Regression modeling', body: 'A numeric target column is available. Consider regression to explain or predict outcomes.' });
    }
    if (state.columns.length >= 4) {
      recommendations.push({ title: 'Feature engineering', body: 'The dataset has enough dimensionality for transformation and feature refinement.' });
    }
    if (!recommendations.length) {
      recommendations.push({ title: 'Data profiling', body: 'Inspect the dataset structure and enrich the available columns before modeling.' });
    }

    list.innerHTML = recommendations.map((item) => `
      <div class="ai-recommendation-card">
        <strong>${escapeHtml(item.title)}</strong>
        <span>${escapeHtml(item.body)}</span>
      </div>
    `).join('');

    explanation.innerHTML = [
      `<li><strong>Data shape</strong><span>${state.rows.length} rows and ${state.columns.length} columns detected.</span></li>`,
      `<li><strong>Numeric readiness</strong><span>${state.numericColumns.length} numeric fields are available for modeling.</span></li>`,
      `<li><strong>Suggested path</strong><span>Start with profiling, then use regression or correlation analysis depending on the target.</span></li>`
    ].join('');
  }

  function bindEvents() {
    document.querySelectorAll('[data-view]').forEach((button) => button.addEventListener('click', () => setView(button.dataset.view)));
    document.querySelectorAll('[data-view-target]').forEach((button) => button.addEventListener('click', () => setView(button.dataset.viewTarget)));
    document.querySelectorAll('[data-method]').forEach((button) => button.addEventListener('click', () => {
      const method = button.dataset.method;
      const methodLabel = button.querySelector('strong')?.textContent || method;
      showToast(`${methodLabel} selected for analysis.`, 'info');
      el('analysisType').value = method === 'descriptive' ? 'descriptive' : method === 'correlation' ? 'correlation' : method === 'regression' ? 'regression' : method === 'hypothesis' ? 'hypothesis' : method === 'time_series' ? 'time_series' : 'classification';
      setView('analysis');
    }));
    el('chooseFile').addEventListener('click', () => el('datasetFile').click());
    el('datasetFile').addEventListener('change', (event) => {
      const file = event.target.files[0];
      if (!file) return;
      loadFile(file);
    });
    el('loadSample').addEventListener('click', () => loadCsvText('sample-health-statistics.csv', sampleCsv));
    el('clearData').addEventListener('click', clearDataset);
    el('uploadToBackend').addEventListener('click', uploadToBackend);
    el('quickAnalyze').addEventListener('click', handleQuickAnalysis);
    el('refreshAiRecommendations').addEventListener('click', () => {
      renderAiRecommendations();
      showToast('AI recommendations refreshed.', 'success');
    });
    el('chartType').addEventListener('change', () => {
      const type = el('chartType').value;
      el('chartColumn2').style.display = (type === 'scatter' || type === 'line') ? 'block' : 'none';
      drawChart();
    });
    el('chartColumn').addEventListener('change', drawChart);
    el('chartColumn2').addEventListener('change', drawChart);
    el('refreshInsights').addEventListener('click', renderInsights);
    el('toggleFilters').addEventListener('click', () => {
      const panel = el('filterPanel');
      panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    });
    el('addFilter').addEventListener('click', addFilter);
    el('clearFilters').addEventListener('click', clearFilters);
    el('dataTable').addEventListener('click', (event) => {
      const th = event.target.closest('th');
      if (th && th.dataset.sort) {
        handleSort(th.dataset.sort);
      }
    });
    el('activeFilters').addEventListener('click', (event) => {
      const button = event.target.closest('button');
      if (button && button.dataset.filterIndex !== undefined) {
        removeFilter(parseInt(button.dataset.filterIndex));
      }
    });
    el('toggleTransforms').addEventListener('click', () => {
      const panel = el('transformPanel');
      panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    });
    el('applyTransform').addEventListener('click', applyTransform);
    el('resetTransforms').addEventListener('click', resetTransforms);
    el('handleOutliers').addEventListener('click', handleOutliers);
    el('clearHistory').addEventListener('click', clearHistory);
    el('runAnalysis').addEventListener('click', runAnalysis);
    el('confidenceRange').addEventListener('input', () => {
      el('confidenceValue').textContent = el('confidenceRange').value + '%';
    });
    el('downloadClean').addEventListener('click', () => {
      if (!state.rows.length) return;
      download((state.name || 'dataset').replace(/\.csv$/i, '') + '-clean.csv', buildCsv(), 'text/csv');
    });
    el('exportReport').addEventListener('click', exportReport);
    el('saveSession').addEventListener('click', saveSession);
    el('loadSession').addEventListener('click', loadSession);
    el('themeToggle').addEventListener('click', () => {
      const dark = document.documentElement.dataset.theme !== 'dark';
      document.documentElement.dataset.theme = dark ? 'dark' : 'light';
      localStorage.setItem('ai-stats-theme', dark ? 'dark' : 'light');
      requestAnimationFrame(drawChart);
    });
    el('tableSearch').addEventListener('input', (event) => {
      const term = event.target.value.trim().toLowerCase();
      state.filteredRows = term ? state.rows.filter((row) => {
        return state.columns.some((column) => column.toLowerCase().includes(term) || String(row[column] ?? '').toLowerCase().includes(term));
      }) : state.rows;
      renderTable();
    });

    const dropZone = el('dropZone');
    ['dragenter', 'dragover'].forEach((name) => dropZone.addEventListener(name, (event) => {
      event.preventDefault();
      dropZone.classList.add('dragging');
    }));
    ['dragleave', 'drop'].forEach((name) => dropZone.addEventListener(name, (event) => {
      event.preventDefault();
      dropZone.classList.remove('dragging');
    }));
    dropZone.addEventListener('drop', (event) => {
      const file = event.dataTransfer.files[0];
      if (file) loadFile(file);
    });
  }

  document.documentElement.dataset.theme = localStorage.getItem('ai-stats-theme') || 'light';
  bindEvents();
  renderAll();
})();
