
'use client';

import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface TimeframeSelectorProps {
  value: string;
  onValueChange: (val: string) => void;
}

export function TimeframeSelector({ value, onValueChange }: TimeframeSelectorProps) {
  const options = [
    { label: '7D', value: '7d' },
    { label: '30D', value: '30d' },
    { label: '90D', value: '90d' },
    { label: 'ALL', value: 'all' },
  ];

  return (
    <Tabs value={value} onValueChange={onValueChange} className="w-fit">
      <TabsList className="bg-elevated/50 p-1 rounded-xl h-10 border border-border-subtle">
        {options.map((opt) => (
          <TabsTrigger 
            key={opt.value} 
            value={opt.value} 
            className="text-[10px] font-black uppercase px-4 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground rounded-lg transition-all"
          >
            {opt.label}
          </TabsTrigger>
        ))}
      </TabsList>
    </Tabs>
  );
}
