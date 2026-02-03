import { useState } from "react";
import { useRouter } from "next/router";
import { api } from "@/lib/api";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isRegister, setIsRegister] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
        if (isRegister) {
            await api.register(email, password);
            alert("Registered! Please login.");
            setIsRegister(false);
        } else {
            const data = await api.login(email, password);
            localStorage.setItem("token", data.access_token);
            router.push("/dashboard");
        }
    } catch (err) {
      alert("Error: " + err.message);
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="w-full max-w-md p-8 bg-white rounded-lg shadow-md text-black">
        <h1 className="text-2xl font-bold mb-6">{isRegister ? "Register" : "Login"}</h1>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <input
            type="email"
            placeholder="Email"
            className="p-2 border rounded"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <input
            type="password"
            placeholder="Password"
            className="p-2 border rounded"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button type="submit" className="p-2 bg-blue-500 text-white rounded">
            {isRegister ? "Register" : "Login"}
          </button>
        </form>
        <button
            className="mt-4 text-blue-500 underline"
            onClick={() => setIsRegister(!isRegister)}
        >
            {isRegister ? "Already have an account? Login" : "Need an account? Register"}
        </button>
      </div>
    </div>
  );
}
