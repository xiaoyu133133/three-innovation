import * as echarts from '../../ec-canvas/echarts';
let chartBar = null; let chartLine = null;

Page({
  data: {
    ecBar: { lazyLoad: true },
    ecLine: { lazyLoad: true }
  },
  onLoad() {
    this.barComponent = this.selectComponent('#mychart-bar');
    this.lineComponent = this.selectComponent('#mychart-line');
    this.initBar(); this.initLine();
  },
  initBar() {
    this.barComponent.init((canvas, width, height, dpr) => {
      chartBar = echarts.init(canvas, null, { width, height, devicePixelRatio: dpr });
      canvas.setChart(chartBar);
      const option = {
        color: ['#1989fa'],
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: '3%', right: '4%', bottom: '3%', top: '15%', containLabel: true },
        xAxis: { type: 'category', data: ['1月','2月','3月','4月','5月','6月'], axisLine: { lineStyle: { color: '#999' } } },
        yAxis: { type: 'value', name: '万度' },
        series: [{ name: '发电量', type: 'bar', barWidth: '40%', data: [5.2, 5.8, 6.5, 7.2, 7.8, 8.1], itemStyle: { borderRadius: [4, 4, 0, 0] } }]
      };
      chartBar.setOption(option); return chartBar;
    });
  },
  initLine() {
    this.lineComponent.init((canvas, width, height, dpr) => {
      chartLine = echarts.init(canvas, null, { width, height, devicePixelRatio: dpr });
      canvas.setChart(chartLine);
      const option = {
        color: ['#07c160', '#ff6700', '#1989fa'],
        tooltip: { trigger: 'axis' },
        legend: { data: ['碳减排(吨)', '收益(万元)', '用电负荷'], bottom: 0, itemWidth: 10, itemHeight: 10 },
        grid: { left: '3%', right: '4%', bottom: '15%', top: '15%', containLabel: true },
        xAxis: { type: 'category', boundaryGap: false, data: ['1月','2月','3月','4月','5月','6月'] },
        yAxis: { type: 'value' },
        series: [
          { name: '碳减排(吨)', type: 'line', smooth: true, data: [51, 57, 64, 71, 77, 80] },
          { name: '收益(万元)', type: 'line', smooth: true, data: [2.6, 2.9, 3.2, 3.6, 3.9, 4.0] },
          { name: '用电负荷', type: 'line', smooth: true, data: [4.8, 4.5, 4.2, 4.0, 5.5, 6.8] } // 夏天负荷升高
        ]
      };
      chartLine.setOption(option); return chartLine;
    });
  }
});