const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = {
  login: async (username: string, password: string) => {
    const formData = new FormData();
    formData.append("username", username);
    formData.append("password", password);

    const res = await fetch(`${API_URL}/auth/token`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) throw new Error("Login failed");
    return res.json();
  },

  register: async (email: string, password: string) => {
    const res = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error("Registration failed");
    return res.json();
  },

  getInstances: async (token: string) => {
    const res = await fetch(`${API_URL}/instances/`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch instances");
    return res.json();
  },

  createInstance: async (token: string, name: string) => {
    const res = await fetch(`${API_URL}/instances/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({ name }),
    });
    if (!res.ok) throw new Error("Failed to create instance");
    return res.json();
  },

  getQRCode: async (token: string, instanceId: number | string) => {
    const res = await fetch(`${API_URL}/instances/${instanceId}/qrcode`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to get QR code");
    return res.json();
  },

  toggleWarming: async (token: string, instanceId: number | string, enable: boolean) => {
      const action = enable ? "start" : "stop";
      const res = await fetch(`${API_URL}/instances/${instanceId}/warming/${action}`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`Failed to ${action} warming`);
      return res.json();
  }
};
