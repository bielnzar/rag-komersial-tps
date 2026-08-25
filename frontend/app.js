const { createApp, ref, nextTick, onMounted } = Vue;

createApp({
    setup() {
        const inputText = ref('');
        const messages = ref([]);
        const isLoading = ref(false);

        const setInput = (text) => {
            inputText.value = text;
        }

        const renderMarkdown = (text) => {
            if (!text) return "";
            // Konfigurasi marked agar tautan terbuka di tab baru
            return marked.parse(text);
        }

        const renderCharts = () => {
            // Beri waktu Vue untuk me-render div kontainer terlebih dahulu
            nextTick(() => {
                messages.value.forEach((msg, index) => {
                    if (msg.role === 'ai' && msg.chart_config) {
                        const chartDom = document.getElementById('chart-' + index);
                        // Cek apakah div chart ada, dan pastikan belum diinisialisasi ECharts sebelumnya
                        if (chartDom && !echarts.getInstanceByDom(chartDom)) {
                            // Inisialisasi echarts dengan tema dark
                            const myChart = echarts.init(chartDom, 'dark');
                            
                            // Modifikasi config dari AI agar background transparan menyatu dengan UI
                            const finalConfig = {
                                ...msg.chart_config,
                                backgroundColor: 'transparent'
                            };
                            
                            myChart.setOption(finalConfig);
                            
                            // Buat chart responsive terhadap ukuran window
                            window.addEventListener('resize', function() {
                                myChart.resize();
                            });
                        }
                    }
                });
            });
        }

        const scrollToBottom = () => {
            nextTick(() => {
                const container = document.getElementById('chat-container');
                if (container) {
                    container.scrollTo({
                        top: container.scrollHeight,
                        behavior: 'smooth'
                    });
                }
            });
        }

        const sendMessage = async () => {
            if (!inputText.value.trim() || isLoading.value) return;

            const userMsg = inputText.value;
            messages.value.push({ role: 'user', text: userMsg });
            inputText.value = ''; // Reset input
            
            isLoading.value = true;
            scrollToBottom();

            try {
                // Memanggil endpoint FastAPI lokal (pastikan backend jalan di port 8000)
                const response = await axios.post('http://127.0.0.1:8000/api/v1/chat', {
                    query: userMsg,
                    user_id: "guest",
                    role: "commercial"
                });

                const data = response.data;
                
                // Tambahkan respon AI ke list obrolan
                messages.value.push({ 
                    role: 'ai', 
                    text: data.answer,
                    chart_config: data.chart_config,
                    sql: data.sql_executed
                });
                
                // Render ECharts (jika ada chart_config)
                renderCharts();

            } catch (error) {
                const errMsg = error.response?.data?.detail || error.message;
                messages.value.push({ 
                    role: 'ai', 
                    text: '⚠️ **Maaf, terjadi kesalahan komunikasi dengan Backend.**\n\nError: `' + errMsg + '`\n\n*Pastikan server Uvicorn berjalan di `localhost:8000`.*' 
                });
            } finally {
                isLoading.value = false;
                scrollToBottom();
            }
        }

        return {
            inputText,
            messages,
            isLoading,
            sendMessage,
            renderMarkdown,
            setInput
        }
    }
}).mount('#app')
