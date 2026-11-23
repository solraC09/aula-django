function lerDados(id) {
    const elemento = document.getElementById(id);
    return elemento ? JSON.parse(elemento.textContent) : [];
}

function desenharBarras(idCanvas, rotulos, valores, horizontal) {
    const canvas = document.getElementById(idCanvas);
    if (!canvas || typeof Chart === 'undefined') {
        return;
    }

    const eixoDosValores = horizontal ? 'x' : 'y';

    new Chart(canvas, {
        type: 'bar',
        data: {
            labels: rotulos,
            datasets: [{
                data: valores,
                backgroundColor: '#5c3a21',
                borderRadius: 3,
            }],
        },
        options: {
            indexAxis: horizontal ? 'y' : 'x',
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                [eixoDosValores]: { beginAtZero: true, ticks: { precision: 0 } },
            },
        },
    });
}

const porMes = lerDados('dados-mes');
desenharBarras('grafico-mes', porMes.map(d => d.mes), porMes.map(d => d.total), false);

const porCategoria = lerDados('dados-categoria');
desenharBarras(
    'grafico-categoria',
    porCategoria.map(d => d.categoria),
    porCategoria.map(d => d.total),
    true,
);
