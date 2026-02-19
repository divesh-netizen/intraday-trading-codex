async function refresh() {
  const [capital, stocks, algos, positions] = await Promise.all([
    fetch('/api/dashboard/capital').then(r => r.json()),
    fetch('/api/stocks').then(r => r.json()),
    fetch('/api/algos').then(r => r.json()),
    fetch('/api/dashboard/positions').then(r => r.json())
  ]);

  document.getElementById('capital').textContent = JSON.stringify(capital, null, 2);
  document.getElementById('stocks').textContent = JSON.stringify(stocks, null, 2);
  document.getElementById('algos').textContent = JSON.stringify(algos, null, 2);
  document.getElementById('positions').textContent = JSON.stringify(positions, null, 2);
}

async function addStock() {
  const symbol = document.getElementById('symbol').value;
  const token = document.getElementById('token').value;
  await fetch('/api/stocks', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ symbol, token })
  });
  await refresh();
}

async function saveAlgo() {
  const payload = JSON.parse(document.getElementById('algo').value);
  await fetch('/api/algos', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  await refresh();
}

setInterval(refresh, 2000);
refresh();
