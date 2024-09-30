// src/MapComponent.jsx
import React, { useState, useRef } from 'react';
import { MapContainer, Polygon, FeatureGroup } from 'react-leaflet';
import { EditControl } from 'react-leaflet-draw';
import "./assets/leaflet.css"
import "./assets/leaflet.draw.css"
import ReactLeafletGoogleLayer from 'react-leaflet-google-layer'
import { Line } from 'react-chartjs-2'
import { format } from 'date-fns';
import L from 'leaflet'
import { es } from 'date-fns/locale'; // Importa el locale español
import { Chart, CategoryScale, LinearScale, LineElement, PointElement } from 'chart.js';
Chart.register(CategoryScale, LinearScale, LineElement, PointElement);


const DrawMap = () => {
  const [positions, setPositions] = useState([]);
  const [data, setDatos] = useState([]);
  const [showChart, setShowChart] = useState(false);
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null); // Referencia para el gráfico
  const [isDragging, setIsDragging] = useState(false);
  const [startPosition, setStartPosition] = useState({ x: 0, y: 0 });
  const [offset, setOffset] = useState({ left: 0, top: 0 });

  const sendCoordinates = async (geometry) => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/ndvi/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({coordinates: [geometry] }),
      });
      const data = await response.json();
      setShowChart(JSON.parse(data))
      setDatos(JSON.parse(data));
    } catch (error) {
      console.error('Error al enviar las coordenadas:', error);
    }
  };

    const _onCreate = (event) => {
      const { layer } = event;
      const newPositions = layer.getLatLngs()[0].map(latlng => [latlng.lng, latlng.lat]);
      setPositions(newPositions);
      
      // Enviar las coordenadas al servidor
      sendCoordinates(newPositions);
    };
    const chartData = { 
      labels: data?.map(entry => format(entry.fecha, 'dd-MM-yyyy', { locale: es })),
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
  // Funciones que permiten mover el gráfico dentro de la ventana
  const handleMouseDown = (e) => {
    setIsDragging(true);
    setStartPosition({ x: e.clientX, y: e.clientY });
  };

  const handleMouseMove = (e) => {
    if (isDragging) {
        const dx = e.clientX - startPosition.x;
        const dy = e.clientY - startPosition.y;

        setOffset((prevOffset) => ({
            left: prevOffset.left + dx,
            top: prevOffset.top + dy,
        }));

        setStartPosition({ x: e.clientX, y: e.clientY });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // Evento de abrir y cerrar gráfico
  const toggleChart = () => {
    setShowChart(prev => !prev); // Alterna la visibilidad del gráfico
  };
  // Descargar gráfico
  const downloadChart = () => {
    const link = document.createElement('a');
    link.href = chartRef.current.toBase64Image(); // Obtiene la imagen en base64
    link.download = 'chart.png'; // Nombre del archivo
    link.click(); // Simula el clic para descargar
  };

  return (
    <div
    onMouseMove={handleMouseMove}
    onMouseUp={handleMouseUp}
    onMouseLeave={handleMouseUp} // Para manejar el caso de salir del contenedor
    >
      <MapContainer center={[-31.5, -60.5]} zoom={7} style={{ height: '93vh', width: '100%', marginTop:'7vh'}}>
        {/* <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        /> */}
        <ReactLeafletGoogleLayer apiKey='AIzaSyBqSKs7DT9oDteBtU5-tgs5t3nxfciLFz0' type={'hybrid'} />
        <div style={{ position: 'absolute', top: '10px', left: '10px', zIndex: 1000 }}>
          <FeatureGroup>
          <EditControl
              style={{ backgroundColor: "blue" }}
              onCreated={_onCreate}
            

              draw={{
                  polyline: {
                      shapeOptions: { color: "red" },
                      allowIntersection: false,
                      showLength: true,
                      metric: false,
                      feet: false
                  },
                  polygon: {
                      allowIntersection: false,
                      shapeOptions: { color: "blue" },
                      edit: false,
                      showLength: true,
                      metric: false,
                      feet: false,
                      showArea: true,
                  },
                  rectangle: {
                      shapeOptions: { color: "green" },
                      showLength: true,
                      metric: false,
                      feet: false,
                      showArea: true
                  },
                  circle: {
                      shapeOptions: { color: "magenta" },
                      showLength: true,
                      metric: false,
                      feet: false,
                      showArea: true
                  },
                  marker: { zIndexOffset: "999", edit: true}
              }}
              // Añadir esta línea para evitar el error
              onDelete={(e) => {
                console.log('Deleted:', e);
              }}
            />
          </FeatureGroup>
          {positions.length > 0 && <Polygon positions={positions} />}
        </div>
        

      </MapContainer>
      {data.length === 0 ? (<div></div>):(<button onClick={toggleChart} style={{ 
                    position: 'absolute',
                    top: '400px',
                    left: '10px',
                    zIndex: 3000,
                    padding: '3px 8px',
                    backgroundColor: 'white',
                    border: '2px solid rgba(0,0,0,0.55)',
                    borderRadius: '3px', }}>
          {showChart ? '⇙' : '⇗'}
      </button>)}
      {data.length === 0 ? (
                <p style={{
                  position: 'absolute',
                  bottom: '20px',
                  right: '20px',
                  color: 'red',
                  backgroundColor: 'rgba(255, 255, 255, 0.8)', // Fondo semi-transparente
                  padding: '10px',
                  borderRadius: '5px',
                  zIndex:2000
              }}>
                  Por favor, dibuje un polígono para generar la gráfica.
              </p>
            ) : (
      showChart && (
                <div ref={chartContainerRef} onMouseDown={handleMouseDown}
                id="chartContainer" style={{
                  position: 'absolute',
                  top: offset.top + 'px',
                  left: offset.left + 'px',
                  background: 'white',
                  padding: '10px',
                  border: '1px solid black',
                  zIndex: 1000,
                  width: '600px',
                  height: '400px',
                  cursor: 'move', // Cambiar el cursor para indicar que es movible
              }}>
                    <Line ref={chartRef} data={chartData} options={{ responsive: true }} />
                    <button onClick={downloadChart} style={{ marginTop: '10px' }}>
                        Descargar Gráfico
                    </button>
                </div>
            ))}
    </div>
  );
};

export default DrawMap;