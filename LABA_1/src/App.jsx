import "./App.css";
import React, { useState } from "react";

function App() {
  const [banned, setBanned] = useState(false);

  const handleBan = () => {
    setBanned(true);
  };

  const handleUnban = () => {
    setBanned(false);
  };

  return (
    <div>
      <span>{banned ? "Пользователь забанен" : "Пользователь не забанен"}</span>
      <br />
      {!banned ? (
        <button onClick={handleBan}>Забанить пользователя</button>
      ) : (
        <button onClick={handleUnban}>Разбанить пользователя</button>
      )}
    </div>
  );
}

export default App;
