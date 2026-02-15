import * as echarts from '../../ec-canvas/echarts';

let chart = null;
// ✅ 新增：用一个变量暂存后端发来的数据
let pendingData = null;

function initChart(canvas, width, height, dpr) {
  chart = echarts.init(canvas, null, {
    width: width,
    height: height,
    devicePixelRatio: dpr
  });
  canvas.setChart(chart);

  const option = {
    grid: { left: '5%', right: '5%', bottom: '5%', top: '15%', containLabel: true },
    tooltip: { show: true, trigger: 'axis' },
    xAxis: { type: 'category', data: [] },
    yAxis: { 
      type: 'value', 
      name: '功率(kW)',
      nameTextStyle: { padding: [0, 0, 0, 10] } 
    },
    series: [{
      data: [],
      type: 'line',
      smooth: true,
      areaStyle: { color: 'rgba(255, 103, 0, 0.2)' },
      itemStyle: { color: '#ff6700' }
    }]
  };

  chart.setOption(option);
  
  // ✅ 关键修复：如果暂存区有数据，立马填进去
  if (pendingData) {
    updateChart(pendingData.categories, pendingData.series);
  }
  
  return chart;
}

// 抽离一个更新图表的函数
function updateChart(categories, seriesData) {
  if (!chart) return;
  chart.setOption({
    xAxis: { data: categories },
    series: [{ data: seriesData }]
  });
}

Page({
  data: {
    ec: { onInit: initChart },
    currentPower: 0,
    maxPower: 0
  },

  onLoad() {
    this.fetchDashboardData();
  },

  fetchDashboardData() {
    // wx.showLoading({ title: '加载中...' }); // 建议注释掉Loading，体验更好
    
    wx.request({
      url: 'http://127.0.0.1:8000/api/dashboard', 
      method: 'GET',
      success: (res) => {
        const result = res.data;
        console.log("后端数据到了：", result);

        this.setData({
          currentPower: result.current_power,
          maxPower: result.max_power
        });

        // ✅ 修复逻辑：
        // 如果 chart 已经好了，直接画
        if (chart) {
          updateChart(result.categories, result.series);
        } else {
          // 如果 chart 还没好，先存起来，等 initChart 醒了自己去拿
          pendingData = {
            categories: result.categories,
            series: result.series
          };
        }
      },
      fail: (err) => {
        console.error(err);
      }
    });
  },

  goToSimulate() {
    wx.navigateTo({ url: '/pages/simulate/simulate' });
  }
});