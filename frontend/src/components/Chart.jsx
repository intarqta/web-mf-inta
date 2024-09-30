import { useState } from "react";
import { Line } from 'react-chartjs-2'
// Registrar las escalas y elementos necesarios
Chart.register(CategoryScale, LinearScale, LineElement, PointElement);

function Chart({data}) {
    const [showChart, setShowChart] = useState(true);
    if(data.length > 0){
        setShowChart(true);
    }{
        console.log('no funciona')
    }
    const chartData = {
        labels: data?.map(entry => entry.fecha),
        datasets: [
            {
                label: 'NDVI',
                data: data.map(entry => entry.NDVI),
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1,
                fill: false,
            },
        ],
    };
    

    return (

        <>
        {showChart && (
                <div id="chartContainer" style={{ position: 'absolute', top: '10px', left: '10px', background: 'white', padding: '10px', border: '1px solid black', zIndex: 1000 }}>
                    <Line data={chartData} options={{ responsive: true }} />
                    <button onClick={() => setShowChart(false)}>Cerrar</button>
                </div>
            )}
        </>
    );
}

export default Chart;