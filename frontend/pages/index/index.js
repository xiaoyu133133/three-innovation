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
    maxPower: 0,
    // ✨ 新增：评分数据相关的状态
    effData: null,
    demoModes: ['优秀', '良好', '一般', '异常'],
    currentModeIndex: 1 // 默认演示“良好”
  },

  onLoad() {
    this.fetchDashboardData();
    this.fetchEfficiencyData('良好'); // 首次加载请求良好状态
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

  // ✨ 新增：手动触发数据同步
  refreshData() {
    wx.showLoading({ title: '正在连接卫星...' });

    wx.request({
      url: 'http://127.0.0.1:8000/api/refresh_prediction', // 调用刚才写的后端接口
      method: 'POST',
      success: (res) => {
        console.log("同步结果：", res.data);
        
        if (res.data.status === 'success') {
          wx.showToast({ title: '同步完成', icon: 'success' });
          
          // 🔄 关键点：数据更新后，立即重新拉取图表数据，让曲线变样！
          this.fetchDashboardData(); 
          
        } else {
          wx.showToast({ title: '同步失败', icon: 'none' });
        }
      },
      fail: (err) => {
        console.error(err);
        wx.showToast({ title: '网络错误', icon: 'none' });
      },
      complete: () => {
        // wx.hideLoading(); // showToast 会自动覆盖 hideLoading，所以这里可以省掉，或者保留
      }
    });
  },

  goToSimulate() {
    wx.navigateTo({ url: '/pages/simulate/simulate' });
  },

  // ✨ 获取效率评分数据，并存入缓存
  fetchEfficiencyData(mode) {
    wx.request({
      url: `http://127.0.0.1:8000/api/efficiency?mode=${mode}`,
      method: 'GET',
      success: (res) => {
        this.setData({
          effData: res.data
        });
        // ✅ 唯一的修改点：将确切的分数存入本地缓存，保证电站信息页数据完全一致
        wx.setStorageSync('currentEffScore', res.data.score);
      }
    });
  },

  // ✨ 新增：演示模式切换按钮（专为答辩准备）
  toggleDemoMode() {
    let nextIndex = this.data.currentModeIndex + 1;
    if (nextIndex >= this.data.demoModes.length) {
      nextIndex = 0;
    }
    const nextMode = this.data.demoModes[nextIndex];
    
    this.setData({ currentModeIndex: nextIndex });
    this.fetchEfficiencyData(nextMode);
    
    wx.showToast({ title: `切换至: ${nextMode}`, icon: 'none' });
  }
});