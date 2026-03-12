import { SignalProof } from '@/lib/types';

export const mockSignalProofs: SignalProof[] = [
  { signalId: 'sig-1', hash: '0x7f8e...3a2b', merkleRoot: '0x1a2b...9f8e', timestamp: new Date().toISOString(), verified: true },
  { signalId: 'sig-2', hash: '0x9a8b...1c2d', merkleRoot: '0x3d4e...5f6g', timestamp: new Date().toISOString(), verified: true }
];
