import { IChartApi, ISeriesApi, UTCTimestamp } from 'lightweight-charts';
import { ChartDrawingEntity, DrawingToolType } from '@/lib/charting/types';

export class CanvasDrawingEngine {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private chart: IChartApi;
  private series: ISeriesApi<any>;
  private drawings: ChartDrawingEntity[] = [];

  private activeTool: DrawingToolType = 'cursor_crosshair';
  private magnetMode: 'off' | 'weak' | 'strong' = 'off';
  private isDrawing = false;
  private currentAnchors: Array<{ time: UTCTimestamp; price: number }> = [];
  private selectedDrawingId: string | null = null;
  private onDrawingsUpdated?: (drawings: ChartDrawingEntity[]) => void;

  constructor(
    canvas: HTMLCanvasElement,
    chart: IChartApi,
    series: ISeriesApi<any>,
    initialDrawings: ChartDrawingEntity[] = [],
    onDrawingsUpdated?: (drawings: ChartDrawingEntity[]) => void
  ) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d')!;
    this.chart = chart;
    this.series = series;
    this.drawings = initialDrawings;
    this.onDrawingsUpdated = onDrawingsUpdated;

    this.bindEvents();
    this.render();
  }

  public setActiveTool(tool: DrawingToolType) {
    this.activeTool = tool;
    this.isDrawing = false;
    this.currentAnchors = [];
    this.render();
  }

  public setMagnetMode(mode: 'off' | 'weak' | 'strong') {
    this.magnetMode = mode;
  }

  public setDrawings(drawings: ChartDrawingEntity[]) {
    this.drawings = drawings;
    this.render();
  }

  public deleteSelected() {
    if (this.selectedDrawingId) {
      this.drawings = this.drawings.filter(d => d.id !== this.selectedDrawingId);
      this.selectedDrawingId = null;
      if (this.onDrawingsUpdated) this.onDrawingsUpdated(this.drawings);
      this.render();
    }
  }

  public clearAll() {
    this.drawings = [];
    this.selectedDrawingId = null;
    if (this.onDrawingsUpdated) this.onDrawingsUpdated(this.drawings);
    this.render();
  }

  private bindEvents() {
    this.canvas.addEventListener('mousedown', this.handleMouseDown.bind(this));
    this.canvas.addEventListener('mousemove', this.handleMouseMove.bind(this));
    this.canvas.addEventListener('mouseup', this.handleMouseUp.bind(this));
  }

  private handleMouseDown(e: MouseEvent) {
    if (this.activeTool.startsWith('cursor_')) {
      // Hit testing for selection
      const rect = this.canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      let foundId: string | null = null;
      for (const d of this.drawings) {
        if (!d.visible || d.anchors.length < 2) continue;
        const p1 = this.domainToScreen(d.anchors[0]);
        const p2 = this.domainToScreen(d.anchors[1]);
        if (!p1 || !p2) continue;

        const dist = this.pointToSegmentDistance(x, y, p1.x, p1.y, p2.x, p2.y);
        if (dist <= 8) {
          foundId = d.id;
          break;
        }
      }
      this.selectedDrawingId = foundId;
      this.render();
      return;
    }

    const domainPoint = this.screenToDomain(e);
    if (!domainPoint) return;

    if (!this.isDrawing) {
      this.isDrawing = true;
      this.currentAnchors = [domainPoint];
    } else {
      // Second anchor commits the drawing
      this.currentAnchors.push(domainPoint);
      const newEntity: ChartDrawingEntity = {
        id: `draw_${Date.now()}`,
        type: this.activeTool,
        instrument: 'ACTIVE',
        anchors: [...this.currentAnchors],
        properties: {
          color: '#2962ff',
          lineWidth: 2,
          lineStyle: 'solid',
          fillColor: 'rgba(41, 98, 255, 0.1)',
        },
        locked: false,
        visible: true,
        zIndex: this.drawings.length + 1,
        createdAt: Date.now(),
        updatedAt: Date.now(),
      };

      this.drawings.push(newEntity);
      this.isDrawing = false;
      this.currentAnchors = [];
      if (this.onDrawingsUpdated) this.onDrawingsUpdated(this.drawings);
      this.render();
    }
  }

  private handleMouseMove(e: MouseEvent) {
    if (!this.isDrawing) return;
    const domainPoint = this.screenToDomain(e);
    if (!domainPoint) return;

    this.render();
    // Render preview line
    const p1 = this.domainToScreen(this.currentAnchors[0]);
    const rect = this.canvas.getBoundingClientRect();
    const x2 = e.clientX - rect.left;
    const y2 = e.clientY - rect.top;

    if (p1) {
      this.ctx.beginPath();
      this.ctx.strokeStyle = '#2962ff';
      this.ctx.lineWidth = 1.5;
      this.ctx.setLineDash([4, 4]);
      this.ctx.moveTo(p1.x, p1.y);
      this.ctx.lineTo(x2, y2);
      this.ctx.stroke();
      this.ctx.setLineDash([]);
    }
  }

  private handleMouseUp() {
    // Handled in click-click model
  }

  private screenToDomain(e: MouseEvent): { time: UTCTimestamp; price: number } | null {
    const rect = this.canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const time = this.chart.timeScale().coordinateToTime(x) as UTCTimestamp | null;
    const price = this.series.coordinateToPrice(y);

    if (!time || price === null) return null;
    return { time, price };
  }

  private domainToScreen(anchor: { time: UTCTimestamp; price: number }): { x: number; y: number } | null {
    const x = this.chart.timeScale().timeToCoordinate(anchor.time);
    const y = this.series.priceToCoordinate(anchor.price);
    if (x === null || y === null) return null;
    return { x, y };
  }

  private pointToSegmentDistance(px: number, py: number, x1: number, y1: number, x2: number, y2: number): number {
    const dx = x2 - x1;
    const dy = y2 - y1;
    const lenSq = dx * dx + dy * dy;
    if (lenSq === 0) return Math.hypot(px - x1, py - y1);
    let t = ((px - x1) * dx + (py - y1) * dy) / lenSq;
    t = Math.max(0, Math.min(1, t));
    return Math.hypot(px - (x1 + t * dx), py - (y1 + t * dy));
  }

  public render() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    for (const d of this.drawings) {
      if (!d.visible || d.anchors.length < 2) continue;
      const p1 = this.domainToScreen(d.anchors[0]);
      const p2 = this.domainToScreen(d.anchors[1]);
      if (!p1 || !p2) continue;

      const isSelected = d.id === this.selectedDrawingId;
      this.ctx.beginPath();
      this.ctx.strokeStyle = isSelected ? '#ff9800' : d.properties.color;
      this.ctx.lineWidth = d.properties.lineWidth || 2;

      if (d.type === 'horizontal_line' || d.type === 'horizontal_ray') {
        this.ctx.moveTo(0, p1.y);
        this.ctx.lineTo(this.canvas.width, p1.y);
      } else if (d.type === 'rectangle') {
        this.ctx.strokeRect(p1.x, p1.y, p2.x - p1.x, p2.y - p1.y);
        this.ctx.fillStyle = d.properties.fillColor || 'rgba(41, 98, 255, 0.1)';
        this.ctx.fillRect(p1.x, p1.y, p2.x - p1.x, p2.y - p1.y);
      } else {
        // Trendline / default
        this.ctx.moveTo(p1.x, p1.y);
        this.ctx.lineTo(p2.x, p2.y);
      }
      this.ctx.stroke();

      // Render anchor handles if selected
      if (isSelected) {
        this.drawAnchorHandle(p1.x, p1.y);
        this.drawAnchorHandle(p2.x, p2.y);
      }
    }
  }

  private drawAnchorHandle(x: number, y: number) {
    this.ctx.beginPath();
    this.ctx.arc(x, y, 4, 0, Math.PI * 2);
    this.ctx.fillStyle = '#ffffff';
    this.ctx.fill();
    this.ctx.lineWidth = 1.5;
    this.ctx.strokeStyle = '#2962ff';
    this.ctx.stroke();
  }

  public resize(width: number, height: number) {
    this.canvas.width = width;
    this.canvas.height = height;
    this.render();
  }
}
