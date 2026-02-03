import React from 'react';

export interface Instance {
  id: number;
  name: string;
  status: string;
  warming_enabled: boolean;
  messages_today: number;
}

interface InstanceCardProps {
  instance: Instance;
  onConnect: (id: number) => void;
  onToggleWarming: (id: number, enable: boolean) => void;
}

export const InstanceCard: React.FC<InstanceCardProps> = ({ instance, onConnect, onToggleWarming }) => {
  return (
    <div className="bg-white p-4 rounded shadow border text-black">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="font-bold text-lg">{instance.name}</h3>
          <p className="text-sm text-gray-500">ID: {instance.id}</p>
        </div>
        <span className={`px-2 py-1 rounded text-xs ${
            instance.status === 'connected' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`}>
            {instance.status}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
          <div>
              <p className="text-gray-500">Messages Today</p>
              <p className="font-medium">{instance.messages_today}</p>
          </div>
          <div>
              <p className="text-gray-500">Warming</p>
              <p className={`font-medium ${instance.warming_enabled ? 'text-green-600' : 'text-gray-400'}`}>
                  {instance.warming_enabled ? 'Active' : 'Inactive'}
              </p>
          </div>
      </div>

      <div className="flex gap-2">
        <button
          onClick={() => onConnect(instance.id)}
          className="flex-1 px-3 py-2 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
        >
          Connect
        </button>
        <button
            onClick={() => onToggleWarming(instance.id, !instance.warming_enabled)}
            className={`flex-1 px-3 py-2 rounded text-sm text-white ${
                instance.warming_enabled ? 'bg-orange-500 hover:bg-orange-600' : 'bg-green-500 hover:bg-green-600'
            }`}
        >
            {instance.warming_enabled ? 'Stop Warming' : 'Start Warming'}
        </button>
      </div>
    </div>
  );
};
