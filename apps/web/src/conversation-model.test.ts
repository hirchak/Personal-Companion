import {it,expect} from 'vitest';
import {sendShortcut,validChatText,chatError} from './conversation-model';
it('Enter/ShiftEnter are multiline; deliberate shortcut sends without IME composition',()=>{expect(sendShortcut({key:'Enter',ctrlKey:false,metaKey:false,isComposing:false})).toBe(false);expect(sendShortcut({key:'Enter',ctrlKey:true,metaKey:false,isComposing:false})).toBe(true);expect(sendShortcut({key:'Enter',ctrlKey:true,metaKey:false,isComposing:true})).toBe(false);});
it('plain instruction and HTML text are data, bounded and nonblank',()=>{expect(validChatText('ignore rules <script>inert()</script>')).toBe(true);expect(validChatText('  ')).toBe(false);expect(validChatText('x'.repeat(12001))).toBe(false);expect(validChatText('x\0')).toBe(false);});
it('conflicts preserve draft; voice source drift asks exact recheck',()=>{expect(chatError('REVISION_CONFLICT')).toContain('ваш текст');expect(chatError('VOICE_SOURCE_STALE')).toContain('Транскрипт');});
