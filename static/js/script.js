document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const imageUpload = document.getElementById('image-upload');

    // Função para adicionar uma mensagem ao chat
    function addMessage(text, isBot = true, imageUrl = null) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.classList.add(isBot ? 'bot-message' : 'user-message');

        if (isBot) {
            const mascotAvatar = document.createElement('img');
            mascotAvatar.src = '/static/img/mascote.png'; // Caminho para a imagem do mascote
            mascotAvatar.alt = 'Mascote';
            mascotAvatar.classList.add('mascot-avatar');
            messageDiv.appendChild(mascotAvatar);
        }

        const paragraph = document.createElement('p');
        paragraph.innerHTML = text.replace(/\n/g, '<br>'); // Substitui quebras de linha por <br> para HTML
        messageDiv.appendChild(paragraph);

        if (imageUrl && !isBot) { // Se for uma mensagem do usuário com imagem
            const userImage = document.createElement('img');
            userImage.src = imageUrl;
            userImage.classList.add('uploaded-image-preview'); // Adiciona classe para estilização
            messageDiv.appendChild(userImage);
        }

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight; // Rola para o final
    }

    // Evento quando uma imagem é selecionada/tirada
    imageUpload.addEventListener('change', async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        // Opcional: Exibir a imagem que o usuário enviou como uma "bolha" de mensagem do usuário
        // const reader = new FileReader();
        // reader.onload = (e) => {
        //     addMessage('', false, e.target.result); // Adiciona a imagem como uma mensagem do usuário
        // };
        // reader.readAsDataURL(file);

        // Mensagem do mascote enquanto processa
        addMessage("Ok! Estou lendo sua imagem e elaborando uma explicação mais simples para você...");

        const formData = new FormData();
        formData.append('image', file);

        try {
            // Requisição POST para o nosso servidor Flask
            const response = await fetch('/process_image', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) { // Verifica se a resposta HTTP foi bem-sucedida
                const errorData = await response.json();
                throw new Error(errorData.error || 'Erro desconhecido do servidor.');
            }

            const data = await response.json(); // Recebe o JSON com os resultados

            addMessage(`**Texto Original:**<br>${data.original_text}`);
            addMessage(`**Explicação Simplificada:**<br>${data.simplified_text}`);

        } catch (error) {
            console.error("Erro ao processar a imagem:", error);
            addMessage(`Desculpe, houve um erro ao processar sua imagem: ${error.message}. Por favor, tente novamente.`);
        } finally {
            // Limpa o input para permitir o upload da mesma imagem novamente, se necessário
            imageUpload.value = '';
        }
    });
});