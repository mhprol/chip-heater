import { useState, useEffect } from "react";
import { useRouter } from "next/router";
import { api } from "@/lib/api";
import { InstanceCard, Instance } from "@/components/InstanceCard";
import { QRCodeScanner } from "@/components/QRCodeScanner";

export default function Dashboard() {
  const [instances, setInstances] = useState<Instance[]>([]);
  const [newInstanceName, setNewInstanceName] = useState("");
  const [showQR, setShowQR] = useState(false);
  const [qrCode, setQrCode] = useState("");
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
      return;
    }
    loadInstances();
  }, []);

  const loadInstances = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) return;
      const data = await api.getInstances(token);
      setInstances(data);
    } catch (err: any) {
      console.error(err);
    }
  };

  const handleCreateInstance = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
        const token = localStorage.getItem("token");
        if (!token) return;
        await api.createInstance(token, newInstanceName);
        setNewInstanceName("");
        loadInstances();
    } catch (err: any) {
        alert("Error creating instance: " + err.message);
    }
  };

  const handleConnect = async (id: number) => {
      try {
          const token = localStorage.getItem("token");
          if (!token) return;
          const data = await api.getQRCode(token, id);
          if (data.qrcode) {
              setQrCode(data.qrcode);
              setShowQR(true);
          } else {
              alert("Could not get QR Code. Instance might be already connected or not ready.");
          }
      } catch (err: any) {
          alert("Error: " + err.message);
      }
  };

  const handleToggleWarming = async (id: number, enable: boolean) => {
      try {
          const token = localStorage.getItem("token");
          if (!token) return;
          await api.toggleWarming(token, id, enable);
          loadInstances();
      } catch (err: any) {
          alert("Error: " + err.message);
      }
  }

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-6xl mx-auto">
        <header className="flex justify-between items-center mb-8">
            <h1 className="text-3xl font-bold">Chip Heater Dashboard</h1>
            <button
                onClick={() => {
                    localStorage.removeItem("token");
                    router.push("/login");
                }}
                className="px-4 py-2 bg-red-500 text-white rounded"
            >
                Logout
            </button>
        </header>

        <div className="mb-8 p-6 bg-white rounded shadow text-black">
            <h2 className="text-xl font-bold mb-4">Add New Instance</h2>
            <form onSubmit={handleCreateInstance} className="flex gap-4">
                <input
                    type="text"
                    placeholder="Instance Name"
                    className="flex-1 p-2 border rounded"
                    value={newInstanceName}
                    onChange={(e) => setNewInstanceName(e.target.value)}
                />
                <button type="submit" className="px-6 py-2 bg-green-500 text-white rounded hover:bg-green-600">
                    Create
                </button>
            </form>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {instances.map((instance) => (
                <InstanceCard
                    key={instance.id}
                    instance={instance}
                    onConnect={handleConnect}
                    onToggleWarming={handleToggleWarming}
                />
            ))}
        </div>
      </div>

      {showQR && (
          <QRCodeScanner qrCode={qrCode} onClose={() => setShowQR(false)} />
      )}
    </div>
  );
}
