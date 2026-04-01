import * as echarts from '../../ec-canvas/echarts';

let chart = null;
// 用一个变量暂存后端发来的数据
let pendingData = null;

function initChart(canvas, width, height, dpr) {
  // 如果已经有了，就不重复初始化
  if (chart) return chart;

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
  
  // 如果暂存区有数据，立马填进去
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
    showChart: true, // ✨ 新增：控制图表是否渲染的开关
    currentPower: 0,
    maxPower: 0,
    effData: null,
    demoModes: ['优秀', '良好', '一般', '异常'],
    currentModeIndex: 1 
  },

  onLoad() {
    this.fetchDashboardData();
    this.fetchEfficiencyData('良好'); 
  },

  // ✨ 核心机制：页面每次出现时重新挂载图表
  onShow() {
    this.setData({ showChart: true });
  },

  // ✨ 核心修复：离开首页（比如去“我的”页面）时，暴力卸载图表！
  onHide() {
    this.setData({ showChart: false });
  },

  fetchDashboardData() {
    // wx.showNavigationBarLoading(); // 建议用这种不打断操作的 Loading
    
    wx.request({
      url: 'https://bd8d882.r9.vip.cpolar.cn/api/dashboard', 
      method: 'GET',
      success: (res) => {
        const result = res.data;
        console.log("后端数据到了：", result);

        this.setData({
          currentPower: result.current_power,
          maxPower: result.max_power
        });

        // 刷新缓存区
        pendingData = {
          categories: result.categories,
          series: result.series
        };

        if (chart) {
          updateChart(result.categories, result.series);
        }
      },
      fail: (err) => {
        console.error(err);
      },
      complete: () => {
        // wx.hideNavigationBarLoading();
      }
    });
  },

  refreshData() {
    wx.showLoading({ title: '正在连接卫星...' });
    wx.request({
      url: 'https://bd8d882.r9.vip.cpolar.cn/api/refresh_prediction', 
      method: 'POST',
      success: (res) => {
        if (res.data.status === 'success') {
          wx.showToast({ title: '同步完成', icon: 'success' });
          wx.removeStorageSync('hasWithdrawnToday');
          this.fetchDashboardData(); 
        } else {
          wx.showToast({ title: '同步失败', icon: 'none' });
        }
      },
      fail: (err) => {
        wx.showToast({ title: '网络错误', icon: 'none' });
      }
    });
  },

  goToSimulate() {
    wx.navigateTo({ url: '/pages/simulate/simulate' });
  },

  fetchEfficiencyData(mode, force = false) {
    wx.request({
      url: `https://bd8d882.r9.vip.cpolar.cn/api/efficiency?mode=${mode}&force=${force}`,
      method: 'GET',
      success: (res) => {
        this.setData({
          effData: res.data
        });
        wx.setStorageSync('currentEffScore', res.data.score);
      }
    });
  },

  toggleDemoMode() {
    let nextIndex = this.data.currentModeIndex + 1;
    if (nextIndex >= this.data.demoModes.length) {
      nextIndex = 0;
    }
    const nextMode = this.data.demoModes[nextIndex];
    
    this.setData({ currentModeIndex: nextIndex });
    this.fetchEfficiencyData(nextMode, true);
    wx.showToast({ title: `切换至: ${nextMode}`, icon: 'none' });
  }
});