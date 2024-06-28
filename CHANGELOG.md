# Changelog

For more recent versions, please refer to the corresponding release on GitHub: https://github.com/stphivos/django-mock-queries/releases

## [v2.1.7](https://github.com/stphivos/django-mock-queries/tree/v2.1.7) (2021-09-12)

[Full Changelog](https://github.com/stphivos/django-mock-queries/compare/v2.1.6...v2.1.7)

**Closed issues:**

- Release date 2.1.6 [\#131](https://github.com/stphivos/django-mock-queries/issues/131)
- Loosen model-bakery dependency [\#130](https://github.com/stphivos/django-mock-queries/issues/130)
- Support for QuerySet.iterator\(\) [\#94](https://github.com/stphivos/django-mock-queries/issues/94)

**Merged pull requests:**

- Improve flaky test for query order by random [\#145](https://github.com/stphivos/django-mock-queries/pull/145) ([stphivos](https://github.com/stphivos))
- Remove dollar sign from example commands [\#144](https://github.com/stphivos/django-mock-queries/pull/144) ([1oglop1](https://github.com/1oglop1))
- Loosen model-bakery dependency [\#140](https://github.com/stphivos/django-mock-queries/pull/140) ([allanlewis](https://github.com/allanlewis))
- Suppress UnorderedObjectListWarning when ordering MockSet [\#139](https://github.com/stphivos/django-mock-queries/pull/139) ([thatguysimon](https://github.com/thatguysimon))

## [v2.1.6](https://github.com/stphivos/django-mock-queries/tree/v2.1.6) (2021-02-21)

[Full Changelog](https://github.com/stphivos/django-mock-queries/compare/v2.1.5...v2.1.6)

**Closed issues:**

- MockSet constructor limited to 11 elements on Python 3.8 [\#125](https://github.com/stphivos/django-mock-queries/issues/125)
- Error if use order\_by random [\#119](https://github.com/stphivos/django-mock-queries/issues/119)
- MockModel never "in" MockSet in Python 2.7  [\#117](https://github.com/stphivos/django-mock-queries/issues/117)
- Limit in MockModel number inside MockSet? [\#113](https://github.com/stphivos/django-mock-queries/issues/113)
- README.md typo [\#106](https://github.com/stphivos/django-mock-queries/issues/106)
- Filter with empty Q object doesn't work as expected [\#102](https://github.com/stphivos/django-mock-queries/issues/102)

**Merged pull requests:**

- Fix tox for ci [\#134](https://github.com/stphivos/django-mock-queries/pull/134) ([mdalp](https://github.com/mdalp))
- Support for QuerySet.iterator\(\) [\#132](https://github.com/stphivos/django-mock-queries/pull/132) ([platonfloria](https://github.com/platonfloria))
- Fix MockSet too many positional arguments error in python 3.8 [\#129](https://github.com/stphivos/django-mock-queries/pull/129) ([stphivos](https://github.com/stphivos))
- Fix bug on empty DjangoQ [\#128](https://github.com/stphivos/django-mock-queries/pull/128) ([stphivos](https://github.com/stphivos))
- Fix order\_by random [\#127](https://github.com/stphivos/django-mock-queries/pull/127) ([stphivos](https://github.com/stphivos))
- Update packages, drop unsupported Django versions with python 2.7, 3.5 [\#126](https://github.com/stphivos/django-mock-queries/pull/126) ([stphivos](https://github.com/stphivos))
- \#106 - add import to README [\#124](https://github.com/stphivos/django-mock-queries/pull/124) ([shinneider](https://github.com/shinneider))
- Build universal wheel [\#122](https://github.com/stphivos/django-mock-queries/pull/122) ([allanlewis](https://github.com/allanlewis))
- Use unittest.mock when available instead of mock. [\#121](https://github.com/stphivos/django-mock-queries/pull/121) ([Gabriel-Fontenelle](https://github.com/Gabriel-Fontenelle))
- Fix the problem that MockModel never "in" MockSet [\#118](https://github.com/stphivos/django-mock-queries/pull/118) ([mapx](https://github.com/mapx))
- Add query named values list [\#116](https://github.com/stphivos/django-mock-queries/pull/116) ([stphivos](https://github.com/stphivos))

## [v2.1.5](https://github.com/stphivos/django-mock-queries/tree/v2.1.5) (2020-05-04)

[Full Changelog](https://github.com/stphivos/django-mock-queries/compare/v2.1.4...v2.1.5)

**Closed issues:**

- Build is broken with pip 20.1 [\#111](https://github.com/stphivos/django-mock-queries/issues/111)
- Add support for Django 3 [\#104](https://github.com/stphivos/django-mock-queries/issues/104)

**Merged pull requests:**

- Remove dependency on internal pip APIs [\#112](https://github.com/stphivos/django-mock-queries/pull/112) ([rbusquet](https://github.com/rbusquet))

## [v2.1.4](https://github.com/stphivos/django-mock-queries/tree/v2.1.4) (2020-03-02)

[Full Changelog](https://github.com/stphivos/django-mock-queries/compare/v2.1.3...v2.1.4)

**Closed issues:**

- Values list doesn't act as expected [\#103](https://github.com/stphivos/django-mock-queries/issues/103)

**Merged pull requests:**

- Add support for Django 3.0.x [\#109](https://github.com/stphivos/django-mock-queries/pull/109) ([stphivos](https://github.com/stphivos))
- Replace model-mommy with model-bakery [\#108](https://github.com/stphivos/django-mock-queries/pull/108) ([stphivos](https://github.com/stphivos))
- Extend get\_field\_values to work for date/datetime objects [\#101](https://github.com/stphivos/django-mock-queries/pull/101) ([brianzhou13](https://github.com/brianzhou13))

## [v2.1.3](https://github.com/stphivos/django-mock-queries/tree/v2.1.3) (2019-05-04)

[Full Changelog](https://github.com/stphivos/django-mock-queries/compare/v2.1.2...v2.1.3)

**Closed issues:**

- Breaking changes in 2.1.2: ignored filtered elements [\#96](https://github.com/stphivos/django-mock-queries/issues/96)

**Merged pull requests:**

- Use compatible release clause in tox deps versions [\#100](https://github.com/stphivos/django-mock-queries/pull/100) ([stphivos](https://github.com/stphivos))
- Add failing test with falsy comparable value [\#99](https://github.com/stphivos/django-mock-queries/pull/99) ([stphivos](https://github.com/stphivos))
- Django Dependency Issues [\#98](https://github.com/stphivos/django-mock-queries/pull/98) ([ish-vasa](https://github.com/ish-vasa))
- Fix 96: check if value is None, and do not rely on boolean conversion [\#97](https://github.com/stphivos/django-mock-queries/pull/97) ([dannywillems](https://github.com/dannywillems))

## [v2.1.2](https://github.com/stphivos/django-mock-queries/tree/v2.1.2) (2019-04-27)

[Full Changelog](https://github.com/stphivos/django-mock-queries/compare/v2.1.1...v2.1.2)

**Closed issues:**

- Mocking serializer: ListSerializer object is not callable [\#91](https://github.com/stphivos/django-mock-queries/issues/91)

**Merged pull requests:**

- Add support for Django 2.2 and Python 3.7 [\#95](https://github.com/stphivos/django-mock-queries/pull/95) ([m3brown](https://github.com/m3brown))
- Exclude none row from filter comparison [\#93](https://github.com/stphivos/django-mock-queries/pull/93) ([stphivos](https://github.com/stphivos))
- Exclude none row from filter comparison [\#92](https://github.com/stphivos/django-mock-queries/pull/92) ([tlfung0219](https://github.com/tlfung0219))

## [v2.1.1](https://github.com/stphivos/django-mock-queries/tree/v2.1.1) (2018-08-09)

[Full Changelog](https://github.com/stphivos/django-mock-queries/compare/v2.1.0...v2.1.1)

## [v2.1.0](https://github.com/stphivos/django-mock-queries/tree/v2.1.0) (2018-08-09)

[Full Changelog](https://github.com/stphivos/django-mock-queries/compare/v2.0.1...v2.1.0)

**Closed issues:**

- MockSet doesn't seem to copy all of its related model's properties. [\#88](https://github.com/stphivos/django-mock-queries/issues/88)

**Merged pull requests:**

- Bump django version lock [\#89](https://github.com/stphivos/django-mock-queries/pull/89) ([dmastylo](https://github.com/dmastylo))
- Fix MockSet empty querysets evaluated to False when converted to bool in py27 [\#87](https://github.com/stphivos/django-mock-queries/pull/87) ([stphivos](https://github.com/stphivos))
- Fix: Empty querysets should be evaluated to False when converted to boolean [\#86](https://github.com/stphivos/django-mock-queries/pull/86) ([mannysz](https://github.com/mannysz))
- Missing range in comparisons list [\#85](https://github.com/stphivos/django-mock-queries/pull/85) ([rbusquet](https://github.com/rbusquet))

## [v2.0.1](https://github.com/stphivos/django-mock-queries/tree/v2.0.1) (2018-05-18)

[Full Changelog](https://github.com/stphivos/django-mock-queries/compare/v2.0.0...v2.0.1)

**Closed issues:**

- Filter by attribute with False value is not working [\#83](https://github.com/stphivos/django-mock-queries/issues/83)
- Plans for releasing `MockSet` as a child of `MagicMock`? [\#81](https://github.com/stphivos/django-mock-queries/issues/81)

**Merged pull requests:**

- Fixing filtering with boolean fields. [\#84](https://github.com/stphivos/django-mock-queries/pull/84) ([zuzelvp](https://github.com/zuzelvp))

## [v2.0.0](https://github.com/stphivos/django-mock-queries/tree/v2.0.0) (2018-04-21)

[Full Changelog](https://github.com/stphivos/django-mock-queries/compare/v1.0.7...v2.0.0)

**Closed issues:**

- Incompatible with pip 10.0.0 [\#80](https://github.com/stphivos/django-mock-queries/issues/80)
- `.distinct\(\)` when using a regular model: 'ModelName has no attribute items` [\#77](https://github.com/stphivos/django-mock-queries/issues/77)

**Merged pull requests:**

- ISSUE-80 Added pip==10.0 compatibility [\#82](https://github.com/stphivos/django-mock-queries/pull/82) ([khudyakovavi](https://github.com/khudyakovavi))
- Adds support for update\_or\_create [\#79](https://github.com/stphivos/django-mock-queries/pull/79) ([rbusquet](https://github.com/rbusquet))
- Fix hash\_dict to use concrete fields with django models [\#78](https://github.com/stphivos/django-mock-queries/pull/78) ([stphivos](https://github.com/stphivos))
- Refactor maintainability issues on complexity part 2 [\#76](https://github.com/stphivos/django-mock-queries/pull/76) ([stphivos](https://github.com/stphivos))
- Refactor maintainability issues on complexity part 1 [\#75](https://github.com/stphivos/django-mock-queries/pull/75) ([stphivos](https://github.com/stphivos))
- Refactor more maintainability issues on duplication [\#74](https://github.com/stphivos/django-mock-queries/pull/74) ([stphivos](https://github.com/stphivos))
- Refactor maintainability issues on duplication [\#73](https://github.com/stphivos/django-mock-queries/pull/73) ([stphivos](https://github.com/stphivos))
- Attempt to improve performance of MockSet by reducing the use of MagicMock. [\#71](https://github.com/stphivos/django-mock-queries/pull/71) ([zuzelvp](https://github.com/zuzelvp))

## [v1.0.7](https://github.com/stphivos/django-mock-queries/tree/v1.0.7) (2018-03-03)

[Full Changelog](https://github.com/stphivos/django-mock-queries/compare/v1.0.6...v1.0.7)

**Closed issues:**

- Support for Django 2.0 [\#69](https://github.com/stphivos/django-mock-queries/issues/69)
- values\(\).distinct\(\)fails with TypeError: unhashable type: 'dict' [\#65](https://github.com/stphivos/django-mock-queries/issues/65)

**Merged pull requests:**

- Add support for Django 2 [\#72](https://github.com/stphivos/django-mock-queries/pull/72) ([stphivos](https://github.com/stphivos))
- Add MockSet write event triggers, improve model mocker orm simulation. [\#70](https://github.com/stphivos/django-mock-queries/pull/70) ([stphivos](https://github.com/stphivos))
- Feature/qs update delete [\#68](https://github.com/stphivos/django-mock-queries/pull/68) ([stphivos](https://github.com/stphivos))
- Omit call to save in MockSet.create [\#67](https://github.com/stphivos/django-mock-queries/pull/67) ([stphivos](https://github.com/stphivos))
- Improving implementation for distinct\(\) [\#66](https://github.com/stphivos/django-mock-queries/pull/66) ([zuzelvp](https://github.com/zuzelvp))

## [v1.0.6](https://github.com/stphivos/django-mock-queries/tree/v1.0.6) (2018-02-13)

[Full Changelog](https://github.com/stphivos/django-mock-queries/compare/v1.0.5...v1.0.6)

**Closed issues:**

- AND operator is not handled properly causing random tests [\#60](https://github.com/stphivos/django-mock-queries/issues/60)

**Merged pull requests:**

- Add python 3.5 to build matrix [\#64](https://github.com/stphivos/django-mock-queries/pull/64) ([stphivos](https://github.com/stphivos))
- Carta issues 60 and false positives [\#63](https://github.com/stphivos/django-mock-queries/pull/63) ([stphivos](https://github.com/stphivos))
- Fix failing test due to hardcoded year value 2017 [\#62](https://github.com/stphivos/django-mock-queries/pull/62) ([stphivos](https://github.com/stphivos))
- Issues 60 AND false positives [\#61](https://github.com/stphivos/django-mock-queries/pull/61) ([zuzelvp](https://github.com/zuzelvp))
- Keep the previous name for decorated methods, functions and classes [\#58](https://github.com/stphivos/django-mock-queries/pull/58) ([grabekm90](https://github.com/grabekm90))

## [v1.0.5](https://github.com/stphivos/django-mock-queries/tree/v1.0.5) (2017-11-30)

[Full Changelog](https://github.com/stphivos/django-mock-queries/compare/v1.0.4...v1.0.5)

## [v1.0.4](https://github.com/stphivos/django-mock-queries/tree/v1.0.4) (2017-11-30)

[Full Changelog](https://github.com/stphivos/django-mock-queries/compare/v1.0.2...v1.0.4)

**Fixed bugs:**

- Support filtering on a values list subquery. [\#54](https://github.com/stphivos/django-mock-queries/pull/54) ([donkirkby](https://github.com/donkirkby))

**Merged pull requests:**

- MockSet earliest/latest fields args [\#57](https://github.com/stphivos/django-mock-queries/pull/57) ([stphivos](https://github.com/stphivos))
- Not obligatory field parameter in latest and earliest query function [\#56](https://github.com/stphivos/django-mock-queries/pull/56) ([grabekm90](https://github.com/grabekm90))
- Fix a missed model parameter for MockSet in ModelMocker [\#55](https://github.com/stphivos/django-mock-queries/pull/55) ([grabekm90](https://github.com/grabekm90))

## [v1.0.2](https://github.com/stphivos/django-mock-queries/tree/v1.0.2) (2017-10-16)

[Full Changelog](https://github.com/stphivos/django-mock-queries/compare/v1.0.0...v1.0.2)

**Merged pull requests:**

- Fix hardcoded requirement to six library [\#53](https://github.com/stphivos/django-mock-queries/pull/53) ([stphivos](https://github.com/stphivos))

## [v1.0.0](https://github.com/stphivos/django-mock-queries/tree/v1.0.0) (2017-10-15)

[Full Changelog](https://github.com/stphivos/django-mock-queries/compare/v0.0.16...v1.0.0)

**Closed issues:**

- Model.objects.create can't take an instance parameter [\#50](https://github.com/stphivos/django-mock-queries/issues/50)
- Q objects with negation [\#48](https://github.com/stphivos/django-mock-queries/issues/48)

**Merged pull requests:**

- Verify support of Django 1.11 [\#52](https://github.com/stphivos/django-mock-queries/pull/52) ([stphivos](https://github.com/stphivos))
- Use function find\_field\_names to determine appropriate field names fo… [\#51](https://github.com/stphivos/django-mock-queries/pull/51) ([stphivos](https://github.com/stphivos))
- Add support for Q objects with negation [\#49](https://github.com/stphivos/django-mock-queries/pull/49) ([stphivos](https://github.com/stphivos))
- Added missing lookups [\#47](https://github.com/stphivos/django-mock-queries/pull/47) ([szykin](https://github.com/szykin))
- dates\(\) and datetimes\(\) support [\#46](https://github.com/stphivos/django-mock-queries/pull/46) ([szykin](https://github.com/szykin))
- Feature/range requirements [\#45](https://github.com/stphivos/django-mock-queries/pull/45) ([stphivos](https://github.com/stphivos))
- Update model-mommy req [\#44](https://github.com/stphivos/django-mock-queries/pull/44) ([orf](https://github.com/orf))

## [v0.0.16](https://github.com/stphivos/django-mock-queries/tree/v0.0.16) (2017-03-14)

[Full Changelog](https://github.com/stphivos/django-mock-queries/compare/v0.0.15...v0.0.16)

**Merged pull requests:**

- Upload v0.0.16 to pypi [\#43](https://github.com/stphivos/django-mock-queries/pull/43) ([stphivos](https://github.com/stphivos))
- Comparisons: regex, iregex, date, datetime rework. [\#42](https://github.com/stphivos/django-mock-queries/pull/42) ([szykin](https://github.com/szykin))
- Fix one-to-many field lookup to use model name [\#41](https://github.com/stphivos/django-mock-queries/pull/41) ([stphivos](https://github.com/stphivos))

## [v0.0.15](https://github.com/stphivos/django-mock-queries/tree/v0.0.15) (2017-03-06)

[Full Changelog](https://github.com/stphivos/django-mock-queries/compare/v0.0.14...v0.0.15)

**Merged pull requests:**

- Update missing qs methods, lookups, aggregations. [\#39](https://github.com/stphivos/django-mock-queries/pull/39) ([stphivos](https://github.com/stphivos))
- Add support for nested fields to values and values\_list [\#38](https://github.com/stphivos/django-mock-queries/pull/38) ([stphivos](https://github.com/stphivos))
- Add support for aggregate on related fields [\#37](https://github.com/stphivos/django-mock-queries/pull/37) ([stphivos](https://github.com/stphivos))
- MockOptions, get\_or\_create\_with defaults [\#36](https://github.com/stphivos/django-mock-queries/pull/36) ([szykin](https://github.com/szykin))
- Add docs todo, remove completed decorators todo. [\#35](https://github.com/stphivos/django-mock-queries/pull/35) ([stphivos](https://github.com/stphivos))
- Add some quirky queries supported by Django: pk is in a subquery and child is equal. [\#34](https://github.com/stphivos/django-mock-queries/pull/34) ([donkirkby](https://github.com/donkirkby))
- Raise specific DoesNotExist exception for the model. [\#32](https://github.com/stphivos/django-mock-queries/pull/32) ([donkirkby](https://github.com/donkirkby))
- Add decorators for unified method patching/replacement [\#31](https://github.com/stphivos/django-mock-queries/pull/31) ([stphivos](https://github.com/stphivos))
- \_meta, values\(\), values\_list\(\) [\#30](https://github.com/stphivos/django-mock-queries/pull/30) ([szykin](https://github.com/szykin))
- Add mocked\_relations decorator for all related models. [\#28](https://github.com/stphivos/django-mock-queries/pull/28) ([donkirkby](https://github.com/donkirkby))

## [v0.0.14](https://github.com/stphivos/django-mock-queries/tree/v0.0.14) (2016-12-15)

[Full Changelog](https://github.com/stphivos/django-mock-queries/compare/v0.0.13...v0.0.14)

**Merged pull requests:**

- Upload v0.0.14 to PyPI [\#25](https://github.com/stphivos/django-mock-queries/pull/25) ([stphivos](https://github.com/stphivos))
- Feature/aggregate multi params [\#24](https://github.com/stphivos/django-mock-queries/pull/24) ([szykin](https://github.com/szykin))
- Mock django db [\#23](https://github.com/stphivos/django-mock-queries/pull/23) ([donkirkby](https://github.com/donkirkby))
- django-rest-framework serializer assert function [\#5](https://github.com/stphivos/django-mock-queries/pull/5) ([stphivos](https://github.com/stphivos))
- Test remaining crud functions and exception scenarios [\#4](https://github.com/stphivos/django-mock-queries/pull/4) ([stphivos](https://github.com/stphivos))
- Test query aggregate, create and get functionality [\#3](https://github.com/stphivos/django-mock-queries/pull/3) ([stphivos](https://github.com/stphivos))
- Fix and test query filtering by q objects [\#2](https://github.com/stphivos/django-mock-queries/pull/2) ([stphivos](https://github.com/stphivos))
- Fix/remove pytest ini [\#1](https://github.com/stphivos/django-mock-queries/pull/1) ([stphivos](https://github.com/stphivos))

## [v0.0.13](https://github.com/stphivos/django-mock-queries/tree/v0.0.13) (2016-06-08)

[Full Changelog](https://github.com/stphivos/django-mock-queries/compare/7c9d6917856d495c15fcee3b058a8e3eecd267b2...v0.0.13)



\* *This Changelog was automatically generated by [github_changelog_generator](https://github.com/github-changelog-generator/github-changelog-generator)*
