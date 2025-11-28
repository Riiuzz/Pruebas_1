import React, { useState } from "react";
import "./App.css";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  // Controla si el chat está abierto o cerrado
  const [isChatOpen, setIsChatOpen] = useState(false);

  // Para mostrar el mensaje de bienvenida solo una vez
  const [hasShownWelcome, setHasShownWelcome] = useState(false);

  // Easter egg: contador de clics en el header y flag para mostrar el mensaje
  const [headerClickCount, setHeaderClickCount] = useState(0);
  const [showEasterEgg, setShowEasterEgg] = useState(false);

  // Abrir el chat (y mensaje de bienvenida la primera vez)
  const handleOpenChat = () => {
    if (!isChatOpen) {
      setIsChatOpen(true);

      if (!hasShownWelcome) {
        const welcomeMessage = {
          from: "bot",
          text:
            "¡Hola! Soy el asistente virtual de Active Research. " +
            "Puedes preguntarme sobre la empresa, metodologías de investigación, " +
            "cotización de proyectos o el pulso ciudadano.",
        };

        setMessages((prev) => {
          if (prev.length === 0) {
            return [...prev, welcomeMessage];
          }
          return prev;
        });

        setHasShownWelcome(true);
      }
    }
  };

  // Maneja los clics en el header 
  const handleHeaderClick = () => {
    if (showEasterEgg) return; 

    const newCount = headerClickCount + 1;
    setHeaderClickCount(newCount);

    // al quinto clic, aparece el mensaje secreto 💗
    if (newCount >= 5) {
      setShowEasterEgg(true);
    }
  };

  // Enviar mensaje al backend
  const handleSend = async (e) => {
    e.preventDefault();

    if (!input.trim()) {
      return;
    }

    const userMessage = {
      from: "user",
      text: input.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch("http://localhost:5000/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: userMessage.text }),
      });

      if (!response.ok) {
        throw new Error("Error en la respuesta del servidor");
      }

      const data = await response.json();

      const botMessage = {
        from: "bot",
        text: `(${data.categoria}) ${data.respuesta}`,
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("Error al llamar al backend:", error);

      const errorMessage = {
        from: "bot",
        text: "Ocurrió un error al procesar tu mensaje.",
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      {}
      <header
        className="app-header"
        onClick={handleHeaderClick}
        title="Active Research Bot"
      >
        <h1>Active Research Bot</h1>
        <p>
          Asistente virtual para consultas sobre estudios de mercado y opinión
          pública de Active Research.
        </p>
      </header>

      {/* Contenido principal con información estática */}
      <main className="layout">
        <section className="info-panel">
          <h2>¿Qué puedes hacer aquí?</h2>
          <p>
            Este bot está diseñado para responder preguntas relacionadas con el
            trabajo de la empresa <strong>Active Research</strong>.
          </p>

          <h3>Temas que entiende el bot</h3>
          <ul>
            <li>
              <span className="badge badge-cat">1</span> Preguntas sobre la
              empresa Active Research.
            </li>
            <li>
              <span className="badge badge-cat">2</span> Preguntas de
              investigación: técnicas, estadísticas, encuestas, metodologías
              (CATI, CAWI, etc.).
            </li>
            <li>
              <span className="badge badge-cat">3</span> Cotización de proyectos
              de estudios de mercado u opinión pública.
            </li>
            <li>
              <span className="badge badge-cat">4</span> Preguntas sobre el
              pulso ciudadano, opinión pública y resultados de encuestas.
            </li>
            <li>
              <span className="badge badge-cat">5</span> Otras preguntas que no
              aplican al contexto del sitio.
            </li>
          </ul>

          <h3>Ejemplos de preguntas</h3>
          <ul className="examples-list">
            <li>“Quiero cotizar un estudio de opinión en Santiago.”</li>
            <li>“¿Qué es la técnica CATI en investigación?”</li>
            <li>“¿Qué tipo de estudios realiza Active Research?”</li>
            <li>
              “¿Cómo está el pulso ciudadano respecto a la aprobación del
              gobierno?”
            </li>
          </ul>

          <p className="disclaimer">
            <strong>Nota:</strong> este bot es parte de un trabajo de título y
            su objetivo es demostrar cómo un asistente web puede filtrar y
            responder consultas de potenciales clientes.
          </p>
        </section>
      </main>

      {/* mensaje romántico secreto */}
      {showEasterEgg && (
        <div className="easter-egg">Te Amo Francisca Morgado</div>
      )}

      {/* Widget flotante abajo a la derecha */}
      <div className="floating-chat">
        {!isChatOpen ? (
          <button className="chat-toggle" onClick={handleOpenChat}>
            <div className="chat-toggle-text">
              <div className="chat-toggle-title">¿Tienes dudas?</div>
              <div className="chat-toggle-subtitle">
                Haz clic aquí para hablar con el asistente de Active Research.
              </div>
            </div>
            <div className="chat-toggle-pill">Abrir chat</div>
          </button>
        ) : (
          <div className="chat-container">
            <div className="chat-header">
              <div>
                <div className="chat-title">Asistente Active Research</div>
                <div className="chat-subtitle">En línea</div>
              </div>
              <button
                className="chat-close"
                type="button"
                onClick={() => setIsChatOpen(false)}
              >
                ×
              </button>
            </div>

            <div className="messages">
              {messages.map((m, index) => (
                <div
                  key={index}
                  className={`message ${
                    m.from === "user" ? "user" : "bot"
                  }`}
                >
                  {m.text}
                </div>
              ))}

              {loading && <div className="message bot">Pensando...</div>}
            </div>

            <form className="input-area" onSubmit={handleSend}>
              <input
                type="text"
                placeholder="Escribe tu pregunta..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
              />
              <button type="submit">Enviar</button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
