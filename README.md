# CASC-Java

A handwritten compiler which can transform English or Manderin, even mixed codes!

“能编译繁简体中文、甚至英语”的编译器，目标是对简体程序员可用。

原项目为 [ChAoS_UnItY](https://github.com/ChAoSUnItY) (Chaos Unity) 开发，由 C# minisk-compiler.net 起意，后者是一个通俗的基础教程示范，也囊括对 IDE 等语言工具 暴露 parser 、 type checker 等“更远的”工作的示范。

此项目为技术交流创建，基于 [C# 版](https://github.com/CASC-Lang/CASC)大体重写，暂无 roadmap ，作为编译器亦无目标语言计划，及源语言规范化文档。

项目有 VSCode 支持计划，但我不会涉及，目标实现语言工具：编译器、REPL。

```plain
一加二十一是二十二 == True
(1 + 9 - 7) 是 (一 加 九 減 七)
1 + 九 減 7
```

相关知识： 算符链 [InfixPattern](https://github.com/ParserKt/ParserKt/blob/master/src/commonMain/kotlin/org/parserkt/pat/complex/InfixPattern.kt)/«Lua设计与实现» 相关章节; 中文数值 [NumUnit](https://github.com/ParserKt/ParserKt/blob/37599098dc9aafef7b509536e6d17ceca370d6cf/parserkt-ext/src/commonMain/kotlin/org/parserkt/pat/ext/NumUnitPattern.kt)/[han()](https://github.com/duangsuse-valid-projects/Share/blob/master/Others/CN_constitution.md)

原项目亦有 [Rust](https://github.com/CASC-Lang/CASC-Rust/blob/main/src/code_parser/syntax/parser.rs#L90) 和 [TypeScript](https://github.com/CASC-Lang/CASC-TS/blob/main/src/codeParser/syntax/Parser.ts) 版，但进度相对落后。

## 关键性质

词法、语法、计算与类型转换、作用域和函数调用。

Op|Traditional|Simplified
:-:|:--|:--
+|加 / 正|
-|減 / 負|减 / 负
/|除
*|乘
.|點|点
&&|且
\|\||或
!|反
==|是
!=|不是
`^2`|平方
`2√`|平方根
`^^`|次方
`√`|開方|开方

[Lexer.cs](https://github.com/CASC-Lang/CASC/tree/master/src/CASC/Lexer.cs): Whitespace `char.IsWhiteSpace` (为 `" \t\n\r"` 优化), Identifier/Keyword `char.IsLetter`, 
整体是 _position, _kind:SyntaxKind 实现的，有趣的是 identifier text 是靠算 span 再 slice 取的，本身倾向流式 `Peek(offset), Current, LookAhead=Peek(1), '\u0000' EOF` 但不完全
第一个 `readonly List<char>` 无使用
写的是： `加 減 乘 除 點 開 閉 正 負 且 或 反(非,!) 是 不(是,!=) 赋(=)` 
开闭括号的我感觉有点奇怪。

```
加正+減負-
乘*除/
(){}
且 &&
或 ||
反!
!= 不是
是==
賦=
```

命名都像 `SyntaxKind.BangEqualsToken(!=) .StarToken(*) .SlashToken(/)` 这样
其中 ==, &&, ||, != 的需消歧义，但没有 lookahead 而是以状态机区分、「不是」「反」「赋」 都是别名

```
0123456789零一二三四五六七八九
壹貳參肆伍陆柒捌玖拾十百千萬億
```
 
靠外置 `ReadNumberToken();` 读数
另外都做了 ReportBadCharacter 的错误记录工作
以上皆返回 `SyntaxToken` ，试用 `SyntaxFacts.GetText` 拿内文，如果则用当前 span 取 substring 。

[Parser.cs](https://github.com/CASC-Lang/CASC/tree/master/src/CASC/Lexer.cs):
CompilationUnit, Stmt, BlockStmt, VariableDeclaration, ExprStmt, VariableDeclaration, Expr, BlockStmt, Stmt, ExprStmt, Expr, Expr, AssignmentExpr, AssignmentExpr, AssignmentExpr, BinaryExpr, BinaryExpr, BinaryExpr, PrimaryExpr, BinaryExpr, PrimaryExpr, ParenthesizedExpr, BooleanExpr, NumberExpr, NameExpr, NumberExpr, ParenthesizedExpr, Expr, BooleanExpr, NameExpr

其中带 Binding(他没解释但估计是作用域上下文，但我很好奇为什么要给每个 Node 键一个 BoundedXXX) 支持的：
BlockStatement, ExpressionStatement, VariableDeclaration
LiteralExpression, VariableExpression, AssignmentExpression, UnaryExpression, BinaryExpression

感觉挺无聊的，还是开始重写吧 🤐
把 Text/Stream, Binding, [ChineseParser.cs](https://github.com/CASC-Lang/CASC/tree/master/src/CASC/CodeParser/Utilities/ChineseParser.cs) 可以改下，或许有其他解决方法。


## 重构部分

> 我是这么想的：除了 `Binding` 的一堆 class 我必须重构，其他代码我尽量保持原义吧
一些设计虽然比较花哨，但也有其可取之处，比如 SourceText,TextLine,TextSpan 那套
而且仿流式&状态机&子程序的 Lexer 与递归下降 Parser ，也算是比较经典的写法

### `XXXBinding`

待定

### `()` Operator

删除，换成 ParenthesizedExpr

### `ChineseParser`

尽量简化、移除无用逻辑和变量
