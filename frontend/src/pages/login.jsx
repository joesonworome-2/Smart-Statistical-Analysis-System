import { useState } from "react";
import {
  signInWithEmailAndPassword,
  signInWithPopup
} from "firebase/auth";

import { auth, googleProvider } from "../firebase";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const loginUser = async (e) => {
    e.preventDefault();

    try {
      await signInWithEmailAndPassword(auth, email, password);
      alert("Login successful");
    } catch (error) {
      alert(error.message);
    }
  };

  const loginWithGoogle = async () => {
    try {
      await signInWithPopup(auth, googleProvider);
      alert("Google login successful");
    } catch (error) {
      alert(error.message);
    }
  };

  return (
    <div>
      <form onSubmit={loginUser}>
        <h2>Login</h2>

        <input
          type="email"
          placeholder="Enter Gmail address"
          onChange={(e) => setEmail(e.target.value)}
        />

        <input
          type="password"
          placeholder="Enter password"
          onChange={(e) => setPassword(e.target.value)}
        />

        <button type="submit">Login</button>
      </form>

      <button onClick={loginWithGoogle}>
        Login with Google Account
      </button>
    </div>
  );
}

export default Login;