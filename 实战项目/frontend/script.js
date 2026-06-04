const API_BASE_URL = 'http://localhost:8000';

let currentResponse = null;

const getFormData = () => {
    const length = document.querySelector('input[name="length"]:checked')?.value || 'medium';
    
    return {
        product_name: document.getElementById('productName').value,
        product_description: document.getElementById('productDesc').value,
        target_audience: document.getElementById('targetAudience').value,
        tone: document.getElementById('tone').value,
        platform: document.getElementById('platform').value,
        length: length
    };
};

const validateForm = (data) => {
    if (!data.product_name.trim()) {
        alert('请输入产品名称');
        return false;
    }
    if (!data.product_description.trim()) {
        alert('请输入产品描述');
        return false;
    }
    if (!data.target_audience.trim()) {
        alert('请输入目标受众');
        return false;
    }
    return true;
};

const showLoading = () => {
    document.getElementById('statusIndicator').style.display = 'flex';
    document.getElementById('outputContent').style.display = 'none';
};

const hideLoading = () => {
    document.getElementById('statusIndicator').style.display = 'none';
    document.getElementById('outputContent').style.display = 'block';
};

const displayResult = (content) => {
    const outputContent = document.getElementById('outputContent');
    outputContent.innerHTML = `<pre style="white-space: pre-wrap; margin: 0; font-family: inherit;">${escapeHtml(content)}</pre>`;
};

const escapeHtml = (text) => {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
};

const generate文案 = async () => {
    const data = getFormData();
    
    if (!validateForm(data)) {
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/generate/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });
        
        if (!response.ok) {
            throw new Error('请求失败');
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let content = '';
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            content += decoder.decode(value, { stream: true });
            displayResult(content);
        }
        
        currentResponse = { content };
        
    } catch (error) {
        console.error('Error:', error);
        alert('生成文案时发生错误，请检查后端服务是否启动');
        displayResult('生成失败，请稍后重试');
    } finally {
        hideLoading();
    }
};

const copyToClipboard = async () => {
    if (!currentResponse) {
        alert('请先生成文案');
        return;
    }
    
    try {
        await navigator.clipboard.writeText(currentResponse.content);
        alert('文案已复制到剪贴板');
    } catch (error) {
        console.error('复制失败:', error);
        alert('复制失败，请手动复制');
    }
};

const regenerate = () => {
    generate文案();
};

document.getElementById('generateBtn').addEventListener('click', generate文案);
document.getElementById('copyBtn').addEventListener('click', copyToClipboard);
document.getElementById('regenerateBtn').addEventListener('click', regenerate);

document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        generate文案();
    }
});

const checkHealth = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const result = await response.json();
        console.log('Service status:', result);
    } catch (error) {
        console.log('Backend service not running, using mock data');
    }
};

checkHealth();