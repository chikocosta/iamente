# TODO - Melhorias no Site AtivaMente

## Fase 2: Análise da área de login atual ✅

### Problemas identificados:
- [ ] ❌ **Rotas de autenticação ausentes**: O app.py não possui rotas `/api/login`, `/api/registro`, `/login`, `/registro`
- [ ] ❌ **Integração frontend-backend**: O login.html chama `/api/login` mas a rota não existe
- [ ] ❌ **Sistema de sessões**: Não há controle de sessão de usuário logado
- [ ] ❌ **Redirecionamento**: Após login não há redirecionamento adequado
- [ ] ❌ **Validação de formulários**: Falta validação robusta no frontend

### Pontos positivos identificados:
- ✅ **Design visual**: Login.html tem design moderno e responsivo
- ✅ **Sistema de usuários**: gerenciador_usuarios.py já implementado com controle de planos
- ✅ **Estrutura de planos**: Free (1/dia), Premium (ilimitado), Escola (ilimitado)

## Fase 3: Implementação do sistema de créditos

### Tarefas pendentes:
- [ ] Implementar rotas de autenticação no app.py
- [ ] Adicionar sistema de sessões Flask
- [ ] Criar middleware para verificar autenticação
- [ ] Implementar controle de créditos baseado no plano
- [ ] Atualizar interface para mostrar créditos restantes
- [ ] Implementar sistema de upgrade de plano
- [ ] Adicionar notificações de limite atingido

## Fase 4: Integração e testes
- [ ] Testar fluxo completo de registro/login
- [ ] Testar limites de geração por plano
- [ ] Verificar responsividade mobile
- [ ] Testar todas as funcionalidades

## Fase 5: Entrega dos resultados
- [ ] Documentar mudanças realizadas
- [ ] Preparar arquivos finais
- [ ] Testar deploy local

