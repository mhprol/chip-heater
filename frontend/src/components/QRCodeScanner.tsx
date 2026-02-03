import React from 'react';

interface QRCodeScannerProps {
  qrCode: string;
  onClose: () => void;
}

export const QRCodeScanner: React.FC<QRCodeScannerProps> = ({ qrCode, onClose }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
      <div className="bg-white p-6 rounded-lg max-w-sm w-full">
        <h3 className="text-lg font-bold mb-4 text-black">Scan QR Code</h3>
        {qrCode ? (
          <img src={qrCode} alt="QR Code" className="w-full h-auto" />
        ) : (
          <p className="text-center text-gray-500">Loading...</p>
        )}
        <button
          onClick={onClose}
          className="mt-4 w-full p-2 bg-gray-200 rounded text-black hover:bg-gray-300"
        >
          Close
        </button>
      </div>
    </div>
  );
};
