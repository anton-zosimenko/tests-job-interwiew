Задание.

Большинство веб-страниц сейчас перегружено всевозможной рекламой... Наша задача «вытащить»
из веб-страницы только полезную информацию, отбросив весь «мусор» (навигацию, рекламу и тд).
Полученный текст нужно отформатировать для максимально комфортного чтения в любом
текстовом редакторе. Правила форматирования: ширина строки не больше 80 символов (если
больше, переносим по словам), абзацы и заголовки отбиваются пустой строкой. Если в тексте
встречаются ссылки, то URL вставить в текст в квадратных скобках. Остальные правила на ваше
усмотрение.
Программа оформляется в виде утилиты командной строки, которой в качестве параметра
указывается произвольный URL. Она извлекает по этому URL страницу, обрабатывает ее и
формирует текстовый файл с текстом статьи, представленной на данной странице.
В качестве примера можно взять любую статью на lenta.ru, gazeta.ru и тд
Алгоритм должен быть максимально универсальным, то есть работать на большинстве сайтов.

Выполнение дополнений – сугубо на ваше усмотрение.
Дополнение 1: Реализуйте решение для удобного хранения файлов, полученных в результате
обработки веб-страниц. Обоснуйте, почему ваше решение будет удобно.
Дополнение 2: Выделять значимые картинки – те, которые относятся к тексту статьи.
Выкладывать эти картинки рядом с файлом-результатом, а в файле оставлять ссылки на картинки
в квадратных скобках.


Описание реализации.

За основу для алгоритма был взят популярный способ разметки сайтов: наличие
блочного тега, содержимое которого оборачивается в строчные. На практике это
выглядит следующим образом: блочный тег <div>, строчные тег(и) <p>, <b>, <a>
и т.д. Первым параметром скрипту передается URL. Парсер проверяет его на
валидность по регулярному выражению
[http://stackoverflow.com/questions/7160737/]. После чего содержимое страницы
по заданному URL фильтруется, и выбирается информация, обрамленная в строчные
теги. Информация фильтруется по количеству слов (не менее 4) для включения в
статью. Заголовок ищется аналогичным образом по заголовочному тегу title.
Кодировка страницы определяется по content-type в заголовке страницы. Содержимое
строчного тега разбивается на слова, из которых набираются строки, не превышающие
80 символов. Содержимое одного строчного тега отделяется от другого путой
строкой. Ссылки внутри статьи определяются, и помещаются в квадратные скобки.

Алгоритм поиска значимой картинки строится на предположении, что в структура
новостной статьи представляет собой заголовок, за ним следует одна или
несколько картинок или фотографий, после чего следует текст статью. Таким
образом ищутся все картинки на странице, после чего для каждой картинки
выясняется размер одним из трех способов: определяются параметры width и height
тега img, при их отсутствии ищется паттерн вида "100х100" в имени файла, при
отсутствии паттерна в имени файла происходит считывание блока 512 байт по ссылке
картинки, после чего с помощью класса Image библиотеки PIL пытаемся получить
размер из заголовочной информации файла картинки. Список картинок сортируется
по площади картинки, причем изображения, с коотношением сторон больше 3
игнорируются (для фильтрации изображений-полос). Картинка с максимальной
площадью скачивается, ссылка на нее помещается в теест статьи в квадратных
скобках между заголовком и телом статьи.

Полученные данные сохраняются в подкаталог downloaded в папку с именем,
полученным из заданного URL с заменой символов '/', ':' и '.' на символ '_'.
Статья сохраняется в файл article.txt, картинка сохраняется с именем, указанным
в теге img. Плюсы такого подхода к хранению файлов: простота реализации,
удобство обращения к файлам, более высокая производительность при обращении (
отсутствуют накладные расходы на обращение к БД и извлечении файлов).

Для выполнения скрипта должны быть установлены следющие пакеты: lmxl,
cssselect, Pillow. Запуск скрипта выполняется из командной строки командой
python script.py <valid URL>. Результаты выполнения скрипта с параметрами:

python script.py http://lenta.ru/news/2015/06/04/opolchenie/
python script.py http://lenta.ru/articles/2015/06/07/gruzia/
python script.py http://lenta.ru/articles/2015/06/05/burdzhanadze/
python script.py http://www.gazeta.ru/style/2010/03/a_3342780.shtml
python script.py http://www.gazeta.ru/politics/2015/06/07_a_6750262.shtml
python script.py http://www.gazeta.ru/vklady_vs_realty/2015/05/06/6670033.shtml
python script.py http://www.newsru.com/russia/07jun2015/ballonclosed.html
python script.py http://www.newsru.com/russia/07jun2015/astrakhan.html
python script.py http://www.newsru.com/russia/07jun2015/deti48.html

приложены в архиве.
Ключевые моменты в коде комментированы ссылками на ресурс, с которого была
почерпнута информация о возможной реализации.