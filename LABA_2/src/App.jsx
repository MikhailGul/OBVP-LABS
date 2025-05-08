import React, { useState } from "react";

function App() {
  const [notes, setNotes] = useState(initNotes);

  const toggleDesc = (id) => {
    setNotes(
      notes.map((note) => {
        if (note.id === id) {
          return { ...note, show: !note.show };
        }
        return note;
      })
    );
  };

  const result = notes.map((note) => (
    <p key={note.id}>
      {note.name}, <i>{note.show ? note.desc : null}</i>
      <button onClick={() => toggleDesc(note.id)}>
        {note.show ? "Hide description" : "Show description"}
      </button>
    </p>
  ));

  return <div>{result}</div>;
}

export default App;
