import { useEffect, useCallback, useRef } from 'react';

const useHotkeys = (hotkeys, dependencies = []) => {
  const hotkeyRef = useRef(new Map());

  // Нормализация комбинации клавиш
  const normalizeHotkey = useCallback((hotkey) => {
    return hotkey
      .toLowerCase()
      .split('+')
      .map(key => key.trim())
      .sort()
      .join('+');
  }, []);

  // Проверка соответствия нажатых клавиш
  const matchesHotkey = useCallback((event, hotkey) => {
    const keys = [];
    
    if (event.ctrlKey || event.metaKey) keys.push('ctrl');
    if (event.altKey) keys.push('alt');
    if (event.shiftKey) keys.push('shift');
    
    // Добавляем основную клавишу
    const key = event.key.toLowerCase();
    if (key !== 'control' && key !== 'alt' && key !== 'shift' && key !== 'meta') {
      keys.push(key);
    }
    
    const pressed = keys.sort().join('+');
    const target = normalizeHotkey(hotkey);
    
    return pressed === target;
  }, [normalizeHotkey]);

  // Обработчик нажатия клавиш
  const handleKeyDown = useCallback((event) => {
    // Игнорируем события в полях ввода (кроме Escape)
    if (event.key !== 'Escape' && (
      event.target.tagName === 'INPUT' ||
      event.target.tagName === 'TEXTAREA' ||
      event.target.contentEditable === 'true'
    )) {
      return;
    }

    hotkeyRef.current.forEach((callback, hotkey) => {
      if (matchesHotkey(event, hotkey)) {
        event.preventDefault();
        event.stopPropagation();
        callback(event);
      }
    });
  }, [matchesHotkey]);

  // Регистрация горячих клавиш
  useEffect(() => {
    hotkeyRef.current.clear();
    
    Object.entries(hotkeys).forEach(([hotkey, callback]) => {
      if (typeof callback === 'function') {
        hotkeyRef.current.set(hotkey, callback);
      }
    });

    document.addEventListener('keydown', handleKeyDown);
    
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown, ...dependencies]);

  return null;
};

export default useHotkeys;