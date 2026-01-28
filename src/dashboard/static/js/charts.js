/**
 * Chart Generation Functions using Plotly
 */

// Get current theme
function getCurrentTheme() {
    return document.documentElement.getAttribute('data-theme') || 'light';
}

// Get theme colors
function getThemeColors() {
    const isDark = getCurrentTheme() === 'dark';
    
    return {
        background: isDark ? '#2d2d2d' : '#ffffff',
        text: isDark ? '#e0e0e0' : '#212529',
        grid: isDark ? '#404040' : '#e5e5e5',
        paper: isDark ? '#1a1a1a' : '#ffffff'
    };
}

// Common layout config
function getCommonLayout(title = '') {
    const colors = getThemeColors();
    
    return {
        title: {
            text: title,
            font: { color: colors.text }
        },
        paper_bgcolor: colors.paper,
        plot_bgcolor: colors.background,
        font: { color: colors.text },
        xaxis: {
            gridcolor: colors.grid,
            color: colors.text
        },
        yaxis: {
            gridcolor: colors.grid,
            color: colors.text
        },
        margin: { t: 30, r: 20, b: 40, l: 60 },
        hovermode: 'closest'
    };
}

// Engagement Chart (Likes & Comments over time)
function createEngagementChart(elementId, data) {
    const colors = getThemeColors();
    
    const trace1 = {
        x: data.dates,
        y: data.likes,
        name: 'Лайки',
        type: 'scatter',
        mode: 'lines+markers',
        line: { color: '#dc3545', width: 3 },
        marker: { size: 6 }
    };
    
    const trace2 = {
        x: data.dates,
        y: data.comments,
        name: 'Коментарі',
        type: 'scatter',
        mode: 'lines+markers',
        line: { color: '#0dcaf0', width: 3 },
        marker: { size: 6 }
    };
    
    const layout = {
        ...getCommonLayout(),
        showlegend: true,
        legend: { orientation: 'h', y: -0.2 }
    };
    
    const config = { responsive: true, displayModeBar: false };
    
    Plotly.newPlot(elementId, [trace1, trace2], layout, config);
}

// Followers Growth Chart
function createFollowersChart(elementId, data) {
    const trace = {
        x: data.dates,
        y: data.followers,
        type: 'scatter',
        mode: 'lines+markers',
        fill: 'tozeroy',
        line: { color: '#0d6efd', width: 3 },
        marker: { size: 6 },
        name: 'Підписники'
    };
    
    const layout = {
        ...getCommonLayout(),
        yaxis: { title: 'Кількість підписників' }
    };
    
    const config = { responsive: true, displayModeBar: false };
    
    Plotly.newPlot(elementId, [trace], layout, config);
}

// Reach & Impressions Chart
function createReachChart(elementId, data) {
    const trace1 = {
        x: data.dates,
        y: data.reach,
        name: 'Охоплення',
        type: 'bar',
        marker: { color: '#0dcaf0' }
    };
    
    const trace2 = {
        x: data.dates,
        y: data.impressions,
        name: 'Покази',
        type: 'bar',
        marker: { color: '#6c757d' }
    };
    
    const layout = {
        ...getCommonLayout(),
        barmode: 'group',
        showlegend: true,
        legend: { orientation: 'h', y: -0.2 }
    };
    
    const config = { responsive: true, displayModeBar: false };
    
    Plotly.newPlot(elementId, [trace1, trace2], layout, config);
}

// Engagement Rate Chart
function createEngagementRateChart(elementId, data) {
    const trace = {
        x: data.dates,
        y: data.engagement,
        type: 'scatter',
        mode: 'lines+markers',
        fill: 'tozeroy',
        line: { color: '#198754', width: 3 },
        marker: { size: 6 },
        name: 'Engagement Rate'
    };
    
    const layout = {
        ...getCommonLayout(),
        yaxis: { title: 'Engagement Rate (%)' }
    };
    
    const config = { responsive: true, displayModeBar: false };
    
    Plotly.newPlot(elementId, [trace], layout, config);
}

// Likes & Comments Chart
function createLikesCommentsChart(elementId, data) {
    const trace1 = {
        x: data.dates,
        y: data.likes,
        name: 'Лайки',
        type: 'bar',
        marker: { color: '#dc3545' }
    };
    
    const trace2 = {
        x: data.dates,
        y: data.comments,
        name: 'Коментарі',
        type: 'bar',
        marker: { color: '#0dcaf0' }
    };
    
    const layout = {
        ...getCommonLayout(),
        barmode: 'stack',
        showlegend: true,
        legend: { orientation: 'h', y: -0.2 }
    };
    
    const config = { responsive: true, displayModeBar: false };
    
    Plotly.newPlot(elementId, [trace1, trace2], layout, config);
}

// Top Posts Chart
function createTopPostsChart(elementId, posts) {
    if (!posts || posts.length === 0) {
        document.getElementById(elementId).innerHTML = '<p class="text-muted text-center">Немає даних</p>';
        return;
    }
    
    const trace = {
        x: posts.map(p => p.engagement_rate),
        y: posts.map((p, i) => `Post ${i + 1}`),
        type: 'bar',
        orientation: 'h',
        marker: {
            color: posts.map(p => p.engagement_rate),
            colorscale: 'Viridis'
        },
        text: posts.map(p => `${p.engagement_rate.toFixed(1)}%`),
        textposition: 'outside'
    };
    
    const layout = {
        ...getCommonLayout(),
        xaxis: { title: 'Engagement Rate (%)' },
        yaxis: { autorange: 'reversed' }
    };
    
    const config = { responsive: true, displayModeBar: false };
    
    Plotly.newPlot(elementId, [trace], layout, config);
}

// Followers Comparison Chart (Competitors)
function createFollowersComparisonChart(elementId, data) {
    const trace = {
        x: data.usernames,
        y: data.followers,
        type: 'bar',
        marker: {
            color: data.followers,
            colorscale: 'Blues'
        },
        text: data.followers.map(f => formatNumber(f)),
        textposition: 'outside'
    };
    
    const layout = {
        ...getCommonLayout(),
        yaxis: { title: 'Підписники' }
    };
    
    const config = { responsive: true, displayModeBar: false };
    
    Plotly.newPlot(elementId, [trace], layout, config);
}

// Engagement Comparison Chart (Competitors)
function createEngagementComparisonChart(elementId, data) {
    const trace = {
        x: data.usernames,
        y: data.engagement_rates,
        type: 'bar',
        marker: {
            color: data.engagement_rates,
            colorscale: 'Greens'
        },
        text: data.engagement_rates.map(e => `${e.toFixed(1)}%`),
        textposition: 'outside'
    };
    
    const layout = {
        ...getCommonLayout(),
        yaxis: { title: 'Engagement Rate (%)' }
    };
    
    const config = { responsive: true, displayModeBar: false };
    
    Plotly.newPlot(elementId, [trace], layout, config);
}

// Posts Activity Chart (Competitors)
function createPostsActivityChart(elementId, data) {
    const trace = {
        x: data.usernames,
        y: data.posts_per_week,
        type: 'bar',
        marker: {
            color: '#ffc107'
        },
        text: data.posts_per_week,
        textposition: 'outside'
    };
    
    const layout = {
        ...getCommonLayout(),
        yaxis: { title: 'Публікацій на тиждень' }
    };
    
    const config = { responsive: true, displayModeBar: false };
    
    Plotly.newPlot(elementId, [trace], layout, config);
}

// Format number helper
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

// Listen for theme changes and update charts
window.addEventListener('themeChanged', (e) => {
    // Reload all visible charts
    const chartElements = document.querySelectorAll('[id$="Chart"]');
    chartElements.forEach(elem => {
        if (elem.data && elem.layout) {
            const layout = { ...elem.layout, ...getCommonLayout() };
            Plotly.relayout(elem.id, layout);
        }
    });
});

// Export functions
window.chartFunctions = {
    createEngagementChart,
    createFollowersChart,
    createReachChart,
    createEngagementRateChart,
    createLikesCommentsChart,
    createTopPostsChart,
    createFollowersComparisonChart,
    createEngagementComparisonChart,
    createPostsActivityChart
};
