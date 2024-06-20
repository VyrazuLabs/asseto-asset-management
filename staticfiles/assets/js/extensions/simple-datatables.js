/******/ (() => { // webpackBootstrap
/******/ 	"use strict";
/******/ 	var __webpack_modules__ = ({

/***/ "./node_modules/simple-datatables/src/columns.js":
/*!*******************************************************!*\
  !*** ./node_modules/simple-datatables/src/columns.js ***!
  \*******************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "Columns": () => (/* binding */ Columns)
/* harmony export */ });
/* harmony import */ var _helpers__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./helpers */ "./node_modules/simple-datatables/src/helpers.js");


/**
 * Columns API
 * @param {Object} instance DataTable instance
 * @param {Mixed} columns  Column index or array of column indexes
 */
class Columns {
    constructor(dt) {
        this.dt = dt
        return this
    }

    /**
     * Swap two columns
     * @return {Void}
     */
    swap(columns) {
        if (columns.length && columns.length === 2) {
            const cols = []

            // Get the current column indexes
            this.dt.headings.forEach((h, i) => {
                cols.push(i)
            })

            const x = columns[0]
            const y = columns[1]
            const b = cols[y]
            cols[y] = cols[x]
            cols[x] = b

            this.order(cols)
        }
    }

    /**
     * Reorder the columns
     * @return {Array} columns  Array of ordered column indexes
     */
    order(columns) {
        let a
        let b
        let c
        let d
        let h
        let s
        let cell

        const temp = [
            [],
            [],
            [],
            []
        ]

        const dt = this.dt

        // Order the headings
        columns.forEach((column, x) => {
            h = dt.headings[column]
            s = h.getAttribute("data-sortable") !== "false"
            a = h.cloneNode(true)
            a.originalCellIndex = x
            a.sortable = s

            temp[0].push(a)

            if (!dt.hiddenColumns.includes(column)) {
                b = h.cloneNode(true)
                b.originalCellIndex = x
                b.sortable = s

                temp[1].push(b)
            }
        })

        // Order the row cells
        dt.data.forEach((row, i) => {
            c = row.cloneNode(false)
            d = row.cloneNode(false)

            c.dataIndex = d.dataIndex = i

            if (row.searchIndex !== null && row.searchIndex !== undefined) {
                c.searchIndex = d.searchIndex = row.searchIndex
            }

            // Append the cell to the fragment in the correct order
            columns.forEach(column => {
                cell = row.cells[column].cloneNode(true)
                cell.data = row.cells[column].data
                c.appendChild(cell)

                if (!dt.hiddenColumns.includes(column)) {
                    cell = row.cells[column].cloneNode(true)
                    cell.data = row.cells[column].data
                    d.appendChild(cell)
                }
            })

            temp[2].push(c)
            temp[3].push(d)
        })

        dt.headings = temp[0]
        dt.activeHeadings = temp[1]

        dt.data = temp[2]
        dt.activeRows = temp[3]

        // Update
        dt.update()
    }

    /**
     * Hide columns
     * @return {Void}
     */
    hide(columns) {
        if (columns.length) {
            const dt = this.dt

            columns.forEach(column => {
                if (!dt.hiddenColumns.includes(column)) {
                    dt.hiddenColumns.push(column)
                }
            })

            this.rebuild()
        }
    }

    /**
     * Show columns
     * @return {Void}
     */
    show(columns) {
        if (columns.length) {
            let index
            const dt = this.dt

            columns.forEach(column => {
                index = dt.hiddenColumns.indexOf(column)
                if (index > -1) {
                    dt.hiddenColumns.splice(index, 1)
                }
            })

            this.rebuild()
        }
    }

    /**
     * Check column(s) visibility
     * @return {Boolean}
     */
    visible(columns) {
        let cols
        const dt = this.dt

        columns = columns || dt.headings.map(th => th.originalCellIndex)

        if (!isNaN(columns)) {
            cols = !dt.hiddenColumns.includes(columns)
        } else if (Array.isArray(columns)) {
            cols = []
            columns.forEach(column => {
                cols.push(!dt.hiddenColumns.includes(column))
            })
        }

        return cols
    }

    /**
     * Add a new column
     * @param {Object} data
     */
    add(data) {
        let td
        const th = document.createElement("th")

        if (!this.dt.headings.length) {
            this.dt.insert({
                headings: [data.heading],
                data: data.data.map(i => [i])
            })
            this.rebuild()
            return
        }

        if (!this.dt.hiddenHeader) {
            if (data.heading.nodeName) {
                th.appendChild(data.heading)
            } else {
                th.innerHTML = data.heading
            }
        } else {
            th.innerHTML = ""
        }

        this.dt.headings.push(th)

        this.dt.data.forEach((row, i) => {
            if (data.data[i]) {
                td = document.createElement("td")

                if (data.data[i].nodeName) {
                    td.appendChild(data.data[i])
                } else {
                    td.innerHTML = data.data[i]
                }

                td.data = td.innerHTML

                if (data.render) {
                    td.innerHTML = data.render.call(this, td.data, td, row)
                }

                row.appendChild(td)
            }
        })

        if (data.type) {
            th.setAttribute("data-type", data.type)
        }
        if (data.format) {
            th.setAttribute("data-format", data.format)
        }

        if (data.hasOwnProperty("sortable")) {
            th.sortable = data.sortable
            th.setAttribute("data-sortable", data.sortable === true ? "true" : "false")
        }

        this.rebuild()

        this.dt.renderHeader()
    }

    /**
     * Remove column(s)
     * @param  {Array|Number} select
     * @return {Void}
     */
    remove(select) {
        if (Array.isArray(select)) {
            // Remove in reverse otherwise the indexes will be incorrect
            select.sort((a, b) => b - a)
            select.forEach(column => this.remove(column))
        } else {
            this.dt.headings.splice(select, 1)

            this.dt.data.forEach(row => {
                row.removeChild(row.cells[select])
            })
        }

        this.rebuild()
    }

    /**
     * Filter by column
     * @param  {int} column - The column no.
     * @param  {string} dir - asc or desc
     * @filter {array} filter - optional parameter with a list of strings
     * @return {void}
     */
    filter(column, dir, init, terms) {
        const dt = this.dt

        // Creates a internal state that manages filters if there are none
        if ( !dt.filterState ) {
            dt.filterState = {
                originalData: dt.data
            }
        }

        // If that column is was not filtered yet, we need to create its state
        if ( !dt.filterState[column] ) {

            // append a filter that selects all rows, 'resetting' the filter
            const filters = [...terms, () => true]

            dt.filterState[column] = (
                function() {
                    let i = 0;
                    return () => filters[i++ % (filters.length)]
                }()
            )
        }

        // Apply the filter and rebuild table
        const rowFilter = dt.filterState[column]() // fetches next filter
        const filteredRows = Array.from(dt.filterState.originalData).filter(tr => {
            const cell = tr.cells[column]
            const content = cell.hasAttribute('data-content') ? cell.getAttribute('data-content') : cell.innerText

            // If the filter is a function, call it, if it is a string, compare it
            return (typeof rowFilter) === 'function' ? rowFilter(content) : content === rowFilter;
        })

        dt.data = filteredRows
        this.rebuild()
        dt.update()
        if (!init) {
            dt.emit("datatable.sort", column, dir)
        }
    }

    /**
     * Sort by column
     * @param  {int} column - The column no.
     * @param  {string} dir - asc or desc
     * @return {void}
     */
    sort(column, dir, init) {
        const dt = this.dt

        // Check column is present
        if (dt.hasHeadings && (column < 0 || column > dt.headings.length)) {
            return false
        }

        //If there is a filter for this column, apply it instead of sorting
        const filterTerms = dt.options.filters &&
              dt.options.filters[dt.headings[column].textContent]
        if ( filterTerms && filterTerms.length !== 0 ) {
            this.filter(column, dir, init, filterTerms)
            return;
        }

        dt.sorting = true

        if (!init) {
            dt.emit("datatable.sorting", column, dir)
        }

        let rows = dt.data
        const alpha = []
        const numeric = []
        let a = 0
        let n = 0
        const th = dt.headings[column]

        const waitFor = []

        // Check for date format
        if (th.getAttribute("data-type") === "date") {
            let format = false
            const formatted = th.hasAttribute("data-format")

            if (formatted) {
                format = th.getAttribute("data-format")
            }
            waitFor.push(__webpack_require__.e(/*! import() */ "node_modules_simple-datatables_src_date_js").then(__webpack_require__.bind(__webpack_require__, /*! ./date */ "./node_modules/simple-datatables/src/date.js")).then(({parseDate}) => date => parseDate(date, format)))
        }

        Promise.all(waitFor).then(importedFunctions => {
            const parseFunction = importedFunctions[0] // only defined if date
            Array.from(rows).forEach(tr => {
                const cell = tr.cells[column]
                const content = cell.hasAttribute('data-content') ? cell.getAttribute('data-content') : cell.innerText
                let num
                if (parseFunction) {
                    num = parseFunction(content)
                } else if (typeof content==="string") {
                    num = content.replace(/(\$|,|\s|%)/g, "")
                } else {
                    num = content
                }

                if (parseFloat(num) == num) {
                    numeric[n++] = {
                        value: Number(num),
                        row: tr
                    }
                } else {
                    alpha[a++] = {
                        value: typeof content==="string" ? content.toLowerCase() : content,
                        row: tr
                    }
                }
            })

            /* Sort according to direction (ascending or descending) */
            if (!dir) {
                if (th.classList.contains("asc")) {
                    dir = "desc"
                } else {
                    dir = "asc"
                }
            }
            let top
            let btm
            if (dir == "desc") {
                top = (0,_helpers__WEBPACK_IMPORTED_MODULE_0__.sortItems)(alpha, -1)
                btm = (0,_helpers__WEBPACK_IMPORTED_MODULE_0__.sortItems)(numeric, -1)
                th.classList.remove("asc")
                th.classList.add("desc")
            } else {
                top = (0,_helpers__WEBPACK_IMPORTED_MODULE_0__.sortItems)(numeric, 1)
                btm = (0,_helpers__WEBPACK_IMPORTED_MODULE_0__.sortItems)(alpha, 1)
                th.classList.remove("desc")
                th.classList.add("asc")
            }

            /* Clear asc/desc class names from the last sorted column's th if it isn't the same as the one that was just clicked */
            if (dt.lastTh && th != dt.lastTh) {
                dt.lastTh.classList.remove("desc")
                dt.lastTh.classList.remove("asc")
            }

            dt.lastTh = th

            /* Reorder the table */
            rows = top.concat(btm)

            dt.data = []
            const indexes = []

            rows.forEach((v, i) => {
                dt.data.push(v.row)

                if (v.row.searchIndex !== null && v.row.searchIndex !== undefined) {
                    indexes.push(i)
                }
            })

            dt.searchData = indexes

            this.rebuild()

            dt.update()

            if (!init) {
                dt.emit("datatable.sort", column, dir)
            }
        })
    }

    /**
     * Rebuild the columns
     * @return {Void}
     */
    rebuild() {
        let a
        let b
        let c
        let d
        const dt = this.dt
        const temp = []

        dt.activeRows = []
        dt.activeHeadings = []

        dt.headings.forEach((th, i) => {
            th.originalCellIndex = i
            th.sortable = th.getAttribute("data-sortable") !== "false"
            if (!dt.hiddenColumns.includes(i)) {
                dt.activeHeadings.push(th)
            }
        })

        // Loop over the rows and reorder the cells
        dt.data.forEach((row, i) => {
            a = row.cloneNode(false)
            b = row.cloneNode(false)

            a.dataIndex = b.dataIndex = i

            if (row.searchIndex !== null && row.searchIndex !== undefined) {
                a.searchIndex = b.searchIndex = row.searchIndex
            }

            // Append the cell to the fragment in the correct order
            Array.from(row.cells).forEach(cell => {
                c = cell.cloneNode(true)
                c.data = cell.data
                a.appendChild(c)

                if (!dt.hiddenColumns.includes(c.cellIndex)) {
                    d = c.cloneNode(true)
                    d.data = c.data
                    b.appendChild(d)
                }
            })

            // Append the fragment with the ordered cells
            temp.push(a)
            dt.activeRows.push(b)
        })

        dt.data = temp

        dt.update()
    }
}


/***/ }),

/***/ "./node_modules/simple-datatables/src/config.js":
/*!******************************************************!*\
  !*** ./node_modules/simple-datatables/src/config.js ***!
  \******************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "defaultConfig": () => (/* binding */ defaultConfig)
/* harmony export */ });
/**
 * Default configuration
 * @typ {Object}
 */
const defaultConfig = {
    sortable: true,
    searchable: true,

    // Pagination
    paging: true,
    perPage: 10,
    perPageSelect: [5, 10, 15, 20, 25],
    nextPrev: true,
    firstLast: false,
    prevText: "&lsaquo;",
    nextText: "&rsaquo;",
    firstText: "&laquo;",
    lastText: "&raquo;",
    ellipsisText: "&hellip;",
    ascText: "▴",
    descText: "▾",
    truncatePager: true,
    pagerDelta: 2,

    scrollY: "",

    fixedColumns: true,
    fixedHeight: false,

    header: true,
    hiddenHeader: false,
    footer: false,

    // Customise the display text
    labels: {
        placeholder: "Search...", // The search input placeholder
        perPage: "{select} entries per page", // per-page dropdown label
        noRows: "No entries found", // Message shown when there are no search results
        info: "Showing {start} to {end} of {rows} entries" //
    },

    // Customise the layout
    layout: {
        top: "{select}{search}",
        bottom: "{info}{pager}"
    }
}


/***/ }),

/***/ "./node_modules/simple-datatables/src/datatable.js":
/*!*********************************************************!*\
  !*** ./node_modules/simple-datatables/src/datatable.js ***!
  \*********************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "DataTable": () => (/* binding */ DataTable)
/* harmony export */ });
/* harmony import */ var _rows__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./rows */ "./node_modules/simple-datatables/src/rows.js");
/* harmony import */ var _columns__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./columns */ "./node_modules/simple-datatables/src/columns.js");
/* harmony import */ var _table__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./table */ "./node_modules/simple-datatables/src/table.js");
/* harmony import */ var _config__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./config */ "./node_modules/simple-datatables/src/config.js");
/* harmony import */ var _helpers__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./helpers */ "./node_modules/simple-datatables/src/helpers.js");







class DataTable {
    constructor(table, options = {}) {
        this.initialized = false

        // user options
        this.options = {
            ..._config__WEBPACK_IMPORTED_MODULE_3__.defaultConfig,
            ...options,
            layout: {
                ..._config__WEBPACK_IMPORTED_MODULE_3__.defaultConfig.layout,
                ...options.layout
            },
            labels: {
                ..._config__WEBPACK_IMPORTED_MODULE_3__.defaultConfig.labels,
                ...options.labels
            }
        }

        if (typeof table === "string") {
            table = document.querySelector(table)
        }

        this.initialLayout = table.innerHTML
        this.initialSortable = this.options.sortable

        // Disable manual sorting if no header is present (#4)
        if (!this.options.header) {
            this.options.sortable = false
        }

        if (table.tHead === null) {
            if (!this.options.data ||
                (this.options.data && !this.options.data.headings)
            ) {
                this.options.sortable = false
            }
        }

        if (table.tBodies.length && !table.tBodies[0].rows.length) {
            if (this.options.data) {
                if (!this.options.data.data) {
                    throw new Error(
                        "You seem to be using the data option, but you've not defined any rows."
                    )
                }
            }
        }

        this.table = table

        this.listeners = {
            onResize: event => this.onResize(event)
        }

        this.init()
    }

    /**
     * Add custom property or method to extend DataTable
     * @param  {String} prop    - Method name or property
     * @param  {Mixed} val      - Function or property value
     * @return {Void}
     */
    static extend(prop, val) {
        if (typeof val === "function") {
            DataTable.prototype[prop] = val
        } else {
            DataTable[prop] = val
        }
    }

    /**
     * Initialize the instance
     * @param  {Object} options
     * @return {Void}
     */
    init(options) {
        if (this.initialized || this.table.classList.contains("dataTable-table")) {
            return false
        }

        Object.assign(this.options, options || {})

        this.currentPage = 1
        this.onFirstPage = true

        this.hiddenColumns = []
        this.columnRenderers = []
        this.selectedColumns = []

        this.render()

        setTimeout(() => {
            this.emit("datatable.init")
            this.initialized = true

            if (this.options.plugins) {
                Object.entries(this.options.plugins).forEach(([plugin, options]) => {
                    if (this[plugin] && typeof this[plugin] === "function") {
                        this[plugin] = this[plugin](options, {createElement: _helpers__WEBPACK_IMPORTED_MODULE_4__.createElement})

                        // Init plugin
                        if (options.enabled && this[plugin].init && typeof this[plugin].init === "function") {
                            this[plugin].init()
                        }
                    }
                })
            }
        }, 10)
    }

    /**
     * Render the instance
     * @param  {String} type
     * @return {Void}
     */
    render(type) {
        if (type) {
            switch (type) {
            case "page":
                this.renderPage()
                break
            case "pager":
                this.renderPager()
                break
            case "header":
                this.renderHeader()
                break
            }

            return false
        }

        const options = this.options
        let template = ""

        // Convert data to HTML
        if (options.data) {
            _table__WEBPACK_IMPORTED_MODULE_2__.dataToTable.call(this)
        }

        // Store references
        this.body = this.table.tBodies[0]
        this.head = this.table.tHead
        this.foot = this.table.tFoot

        if (!this.body) {
            this.body = (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.createElement)("tbody")

            this.table.appendChild(this.body)
        }

        this.hasRows = this.body.rows.length > 0

        // Make a tHead if there isn't one (fixes #8)
        if (!this.head) {
            const h = (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.createElement)("thead")
            const t = (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.createElement)("tr")

            if (this.hasRows) {
                Array.from(this.body.rows[0].cells).forEach(() => {
                    t.appendChild((0,_helpers__WEBPACK_IMPORTED_MODULE_4__.createElement)("th"))
                })

                h.appendChild(t)
            }

            this.head = h

            this.table.insertBefore(this.head, this.body)

            this.hiddenHeader = options.hiddenHeader
        }

        this.headings = []
        this.hasHeadings = this.head.rows.length > 0

        if (this.hasHeadings) {
            this.header = this.head.rows[0]
            this.headings = [].slice.call(this.header.cells)
        }

        // Header
        if (!options.header) {
            if (this.head) {
                this.table.removeChild(this.table.tHead)
            }
        }

        // Footer
        if (options.footer) {
            if (this.head && !this.foot) {
                this.foot = (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.createElement)("tfoot", {
                    html: this.head.innerHTML
                })
                this.table.appendChild(this.foot)
            }
        } else {
            if (this.foot) {
                this.table.removeChild(this.table.tFoot)
            }
        }

        // Build
        this.wrapper = (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.createElement)("div", {
            class: "dataTable-wrapper dataTable-loading"
        })

        // Template for custom layouts
        template += "<div class='dataTable-top'>"
        template += options.layout.top
        template += "</div>"
        if (options.scrollY.length) {
            template += `<div class='dataTable-container' style='height: ${options.scrollY}; overflow-Y: auto;'></div>`
        } else {
            template += "<div class='dataTable-container'></div>"
        }
        template += "<div class='dataTable-bottom'>"
        template += options.layout.bottom
        template += "</div>"

        // Info placement
        template = template.replace("{info}", options.paging ? "<div class='dataTable-info'></div>" : "")

        // Per Page Select
        if (options.paging && options.perPageSelect) {
            let wrap = "<div class='dataTable-dropdown'><label>"
            wrap += options.labels.perPage
            wrap += "</label></div>"

            // Create the select
            const select = (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.createElement)("select", {
                class: "dataTable-selector"
            })

            // Create the options
            options.perPageSelect.forEach(val => {
                const selected = val === options.perPage
                const option = new Option(val, val, selected, selected)
                select.add(option)
            })

            // Custom label
            wrap = wrap.replace("{select}", select.outerHTML)

            // Selector placement
            template = template.replace("{select}", wrap)
        } else {
            template = template.replace("{select}", "")
        }

        // Searchable
        if (options.searchable) {
            const form =
                `<div class='dataTable-search'><input class='dataTable-input' placeholder='${options.labels.placeholder}' type='text'></div>`

            // Search input placement
            template = template.replace("{search}", form)
        } else {
            template = template.replace("{search}", "")
        }

        if (this.hasHeadings) {
            // Sortable
            this.render("header")
        }

        // Add table class
        this.table.classList.add("dataTable-table")

        // Paginator
        const paginatorWrapper = (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.createElement)("nav", {
            class: "dataTable-pagination"
        })
        const paginator = (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.createElement)("ul", {
            class: "dataTable-pagination-list"
        })
        paginatorWrapper.appendChild(paginator)

        // Pager(s) placement
        template = template.replace(/\{pager\}/g, paginatorWrapper.outerHTML)
        this.wrapper.innerHTML = template

        this.container = this.wrapper.querySelector(".dataTable-container")

        this.pagers = this.wrapper.querySelectorAll(".dataTable-pagination-list")

        this.label = this.wrapper.querySelector(".dataTable-info")

        // Insert in to DOM tree
        this.table.parentNode.replaceChild(this.wrapper, this.table)
        this.container.appendChild(this.table)

        // Store the table dimensions
        this.rect = this.table.getBoundingClientRect()

        // Convert rows to array for processing
        this.data = Array.from(this.body.rows)
        this.activeRows = this.data.slice()
        this.activeHeadings = this.headings.slice()

        // Update
        this.update()


        this.setColumns()


        // Fix height
        this.fixHeight()

        // Fix columns
        this.fixColumns()

        // Class names
        if (!options.header) {
            this.wrapper.classList.add("no-header")
        }

        if (!options.footer) {
            this.wrapper.classList.add("no-footer")
        }

        if (options.sortable) {
            this.wrapper.classList.add("sortable")
        }

        if (options.searchable) {
            this.wrapper.classList.add("searchable")
        }

        if (options.fixedHeight) {
            this.wrapper.classList.add("fixed-height")
        }

        if (options.fixedColumns) {
            this.wrapper.classList.add("fixed-columns")
        }

        this.bindEvents()
    }

    /**
     * Render the page
     * @return {Void}
     */
    renderPage() {
        if (this.hasHeadings) {
            (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.flush)(this.header)

            this.activeHeadings.forEach(th => this.header.appendChild(th))
        }


        if (this.hasRows && this.totalPages) {
            if (this.currentPage > this.totalPages) {
                this.currentPage = 1
            }

            // Use a fragment to limit touching the DOM
            const index = this.currentPage - 1

            const frag = document.createDocumentFragment()
            this.pages[index].forEach(row => frag.appendChild(this.rows().render(row)))

            this.clear(frag)

            this.onFirstPage = this.currentPage === 1
            this.onLastPage = this.currentPage === this.lastPage
        } else {
            this.setMessage(this.options.labels.noRows)
        }

        // Update the info
        let current = 0

        let f = 0
        let t = 0
        let items

        if (this.totalPages) {
            current = this.currentPage - 1
            f = current * this.options.perPage
            t = f + this.pages[current].length
            f = f + 1
            items = this.searching ? this.searchData.length : this.data.length
        }

        if (this.label && this.options.labels.info.length) {
            // CUSTOM LABELS
            const string = this.options.labels.info
                .replace("{start}", f)
                .replace("{end}", t)
                .replace("{page}", this.currentPage)
                .replace("{pages}", this.totalPages)
                .replace("{rows}", items)

            this.label.innerHTML = items ? string : ""
        }

        if (this.currentPage == 1) {
            this.fixHeight()
        }
    }

    /**
     * Render the pager(s)
     * @return {Void}
     */
    renderPager() {
        (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.flush)(this.pagers)

        if (this.totalPages > 1) {
            const c = "pager"
            const frag = document.createDocumentFragment()
            const prev = this.onFirstPage ? 1 : this.currentPage - 1
            const next = this.onLastPage ? this.totalPages : this.currentPage + 1

            // first button
            if (this.options.firstLast) {
                frag.appendChild((0,_helpers__WEBPACK_IMPORTED_MODULE_4__.button)(c, 1, this.options.firstText))
            }

            // prev button
            if (this.options.nextPrev) {
                frag.appendChild((0,_helpers__WEBPACK_IMPORTED_MODULE_4__.button)(c, prev, this.options.prevText))
            }

            let pager = this.links

            // truncate the links
            if (this.options.truncatePager) {
                pager = (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.truncate)(
                    this.links,
                    this.currentPage,
                    this.pages.length,
                    this.options.pagerDelta,
                    this.options.ellipsisText
                )
            }

            // active page link
            this.links[this.currentPage - 1].classList.add("active")

            // append the links
            pager.forEach(p => {
                p.classList.remove("active")
                frag.appendChild(p)
            })

            this.links[this.currentPage - 1].classList.add("active")

            // next button
            if (this.options.nextPrev) {
                frag.appendChild((0,_helpers__WEBPACK_IMPORTED_MODULE_4__.button)(c, next, this.options.nextText))
            }

            // first button
            if (this.options.firstLast) {
                frag.appendChild((0,_helpers__WEBPACK_IMPORTED_MODULE_4__.button)(c, this.totalPages, this.options.lastText))
            }

            // We may have more than one pager
            this.pagers.forEach(pager => {
                pager.appendChild(frag.cloneNode(true))
            })
        }
    }

    /**
     * Render the header
     * @return {Void}
     */
    renderHeader() {
        this.labels = []

        if (this.headings && this.headings.length) {
            this.headings.forEach((th, i) => {

                this.labels[i] = th.textContent

                if (th.firstElementChild && th.firstElementChild.classList.contains("dataTable-sorter")) {
                    th.innerHTML = th.firstElementChild.innerHTML
                }

                th.sortable = th.getAttribute("data-sortable") !== "false"

                th.originalCellIndex = i
                if (this.options.sortable && th.sortable) {
                    const link = (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.createElement)("a", {
                        href: "#",
                        class: "dataTable-sorter",
                        html: th.innerHTML
                    })

                    th.innerHTML = ""
                    th.setAttribute("data-sortable", "")
                    th.appendChild(link)
                }
            })
        }

        this.fixColumns()
    }

    /**
     * Bind event listeners
     * @return {[type]} [description]
     */
    bindEvents() {
        const options = this.options
        // Per page selector
        if (options.perPageSelect) {
            const selector = this.wrapper.querySelector(".dataTable-selector")
            if (selector) {
                // Change per page
                selector.addEventListener("change", () => {
                    options.perPage = parseInt(selector.value, 10)
                    this.update()

                    this.fixHeight()

                    this.emit("datatable.perpage", options.perPage)
                }, false)
            }
        }

        // Search input
        if (options.searchable) {
            this.input = this.wrapper.querySelector(".dataTable-input")
            if (this.input) {
                this.input.addEventListener("keyup", () => this.search(this.input.value), false)
            }
        }

        // Pager(s) / sorting
        this.wrapper.addEventListener("click", e => {
            const t = e.target.closest('a')
            if (t && (t.nodeName.toLowerCase() === "a")) {
                if (t.hasAttribute("data-page")) {
                    this.page(t.getAttribute("data-page"))
                    e.preventDefault()
                } else if (
                    options.sortable &&
                    t.classList.contains("dataTable-sorter") &&
                    t.parentNode.getAttribute("data-sortable") != "false"
                ) {
                    this.columns().sort(this.headings.indexOf(t.parentNode))
                    e.preventDefault()
                }
            }
        }, false)

        window.addEventListener("resize", this.listeners.onResize)
    }

    /**
     * execute on resize
     */
    onResize() {
        this.rect = this.container.getBoundingClientRect()
        if (!this.rect.width) {
            // No longer shown, likely no longer part of DOM. Give up.
            return
        }
        this.fixColumns()
    }

    /**
     * Set up columns
     * @return {[type]} [description]
     */
    setColumns(ajax) {

        if (!ajax) {
            this.data.forEach(row => {
                Array.from(row.cells).forEach(cell => {
                    cell.data = cell.innerHTML
                })
            })
        }

        // Check for the columns option
        if (this.options.columns && this.headings.length) {

            this.options.columns.forEach(data => {

                // convert single column selection to array
                if (!Array.isArray(data.select)) {
                    data.select = [data.select]
                }

                if (data.hasOwnProperty("render") && typeof data.render === "function") {
                    this.selectedColumns = this.selectedColumns.concat(data.select)

                    this.columnRenderers.push({
                        columns: data.select,
                        renderer: data.render
                    })
                }

                // Add the data attributes to the th elements
                data.select.forEach(column => {
                    const th = this.headings[column]
                    if (data.type) {
                        th.setAttribute("data-type", data.type)
                    }
                    if (data.format) {
                        th.setAttribute("data-format", data.format)
                    }
                    if (data.hasOwnProperty("sortable")) {
                        th.setAttribute("data-sortable", data.sortable)
                    }

                    if (data.hasOwnProperty("hidden")) {
                        if (data.hidden !== false) {
                            this.columns().hide([column])
                        }
                    }

                    if (data.hasOwnProperty("sort") && data.select.length === 1) {
                        this.columns().sort(data.select[0], data.sort, true)
                    }
                })
            })
        }

        if (this.hasRows) {
            this.data.forEach((row, i) => {
                row.dataIndex = i
                Array.from(row.cells).forEach(cell => {
                    cell.data = cell.innerHTML
                })
            })

            if (this.selectedColumns.length) {
                this.data.forEach(row => {
                    Array.from(row.cells).forEach((cell, i) => {
                        if (this.selectedColumns.includes(i)) {
                            this.columnRenderers.forEach(options => {
                                if (options.columns.includes(i)) {
                                    cell.innerHTML = options.renderer.call(this, cell.data, cell, row)
                                }
                            })
                        }
                    })
                })
            }

            this.columns().rebuild()
        }

        this.render("header")
    }

    /**
     * Destroy the instance
     * @return {void}
     */
    destroy() {
        this.table.innerHTML = this.initialLayout

        // Remove the className
        this.table.classList.remove("dataTable-table")

        // Remove the containers
        this.wrapper.parentNode.replaceChild(this.table, this.wrapper)

        this.initialized = false

        window.removeEventListener("resize", this.listeners.onResize)
    }

    /**
     * Update the instance
     * @return {Void}
     */
    update() {
        this.wrapper.classList.remove("dataTable-empty")

        this.paginate(this)
        this.render("page")

        this.links = []

        let i = this.pages.length
        while (i--) {
            const num = i + 1
            this.links[i] = (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.button)(i === 0 ? "active" : "", num, num)
        }

        this.sorting = false

        this.render("pager")

        this.rows().update()

        this.emit("datatable.update")
    }

    /**
     * Sort rows into pages
     * @return {Number}
     */
    paginate() {
        const perPage = this.options.perPage
        let rows = this.activeRows

        if (this.searching) {
            rows = []

            this.searchData.forEach(index => rows.push(this.activeRows[index]))
        }

        if (this.options.paging) {
            // Check for hidden columns
            this.pages = rows
                .map((tr, i) => i % perPage === 0 ? rows.slice(i, i + perPage) : null)
                .filter(page => page)
        } else {
            this.pages = [rows]
        }

        this.totalPages = this.lastPage = this.pages.length

        return this.totalPages
    }

    /**
     * Fix column widths
     * @return {Void}
     */
    fixColumns() {

        if ((this.options.scrollY.length || this.options.fixedColumns) && this.activeHeadings && this.activeHeadings.length) {
            let cells
            let hd = false
            this.columnWidths = []

            // If we have headings we need only set the widths on them
            // otherwise we need a temp header and the widths need applying to all cells
            if (this.table.tHead) {

                if (this.options.scrollY.length) {
                    hd = (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.createElement)("thead")
                    hd.appendChild((0,_helpers__WEBPACK_IMPORTED_MODULE_4__.createElement)("tr"))
                    hd.style.height = '0px'
                    if (this.headerTable) {
                        // move real header back into place
                        this.table.tHead = this.headerTable.tHead
                    }
                }

                // Reset widths
                this.activeHeadings.forEach(cell => {
                    cell.style.width = ""
                })

                this.activeHeadings.forEach((cell, i) => {
                    const ow = cell.offsetWidth
                    const w = ow / this.rect.width * 100
                    cell.style.width = `${w}%`
                    this.columnWidths[i] = ow
                    if (this.options.scrollY.length) {
                        const th = (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.createElement)("th")
                        hd.firstElementChild.appendChild(th)
                        th.style.width = `${w}%`
                        th.style.paddingTop = "0"
                        th.style.paddingBottom = "0"
                        th.style.border = "0"
                    }
                })

                if (this.options.scrollY.length) {
                    const container = this.table.parentElement
                    if (!this.headerTable) {
                        this.headerTable = (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.createElement)("table", {
                            class: "dataTable-table"
                        })
                        const headercontainer = (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.createElement)("div", {
                            class: "dataTable-headercontainer"
                        })
                        headercontainer.appendChild(this.headerTable)
                        container.parentElement.insertBefore(headercontainer, container)
                    }
                    const thd = this.table.tHead
                    this.table.replaceChild(hd, thd)
                    this.headerTable.tHead = thd

                    // Compensate for scrollbars.
                    this.headerTable.parentElement.style.paddingRight = `${
                        this.headerTable.clientWidth -
                        this.table.clientWidth +
                        parseInt(
                            this.headerTable.parentElement.style.paddingRight ||
                            '0',
                            10
                        )
                    }px`

                    if (container.scrollHeight > container.clientHeight) {
                        // scrollbars on one page means scrollbars on all pages.
                        container.style.overflowY = 'scroll'
                    }
                }

            } else {
                cells = []

                // Make temperary headings
                hd = (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.createElement)("thead")
                const r = (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.createElement)("tr")
                Array.from(this.table.tBodies[0].rows[0].cells).forEach(() => {
                    const th = (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.createElement)("th")
                    r.appendChild(th)
                    cells.push(th)
                })

                hd.appendChild(r)
                this.table.insertBefore(hd, this.body)

                const widths = []
                cells.forEach((cell, i) => {
                    const ow = cell.offsetWidth
                    const w = ow / this.rect.width * 100
                    widths.push(w)
                    this.columnWidths[i] = ow
                })

                this.data.forEach(row => {
                    Array.from(row.cells).forEach((cell, i) => {
                        if (this.columns(cell.cellIndex).visible())
                            cell.style.width = `${widths[i]}%`
                    })
                })

                // Discard the temp header
                this.table.removeChild(hd)
            }
        }
    }

    /**
     * Fix the container height
     * @return {Void}
     */
    fixHeight() {
        if (this.options.fixedHeight) {
            this.container.style.height = null
            this.rect = this.container.getBoundingClientRect()
            this.container.style.height = `${this.rect.height}px`
        }
    }

    /**
     * Perform a search of the data set
     * @param  {string} query
     * @return {void}
     */
    search(query) {
        if (!this.hasRows) return false

        query = query.toLowerCase()

        this.currentPage = 1
        this.searching = true
        this.searchData = []

        if (!query.length) {
            this.searching = false
            this.update()
            this.emit("datatable.search", query, this.searchData)
            this.wrapper.classList.remove("search-results")
            return false
        }

        this.clear()

        this.data.forEach((row, idx) => {
            const inArray = this.searchData.includes(row)

            // https://github.com/Mobius1/Vanilla-DataTables/issues/12
            const doesQueryMatch = query.split(" ").reduce((bool, word) => {
                let includes = false
                let cell = null
                let content = null

                for (let x = 0; x < row.cells.length; x++) {
                    cell = row.cells[x]
                    content = cell.hasAttribute('data-content') ? cell.getAttribute('data-content') : cell.textContent

                    if (
                        content.toLowerCase().includes(word) &&
                        this.columns(cell.cellIndex).visible()
                    ) {
                        includes = true
                        break
                    }
                }

                return bool && includes
            }, true)

            if (doesQueryMatch && !inArray) {
                row.searchIndex = idx
                this.searchData.push(idx)
            } else {
                row.searchIndex = null
            }
        })

        this.wrapper.classList.add("search-results")

        if (!this.searchData.length) {
            this.wrapper.classList.remove("search-results")

            this.setMessage(this.options.labels.noRows)
        } else {
            this.update()
        }

        this.emit("datatable.search", query, this.searchData)
    }

    /**
     * Change page
     * @param  {int} page
     * @return {void}
     */
    page(page) {
        // We don't want to load the current page again.
        if (page == this.currentPage) {
            return false
        }

        if (!isNaN(page)) {
            this.currentPage = parseInt(page, 10)
        }

        if (page > this.pages.length || page < 0) {
            return false
        }

        this.render("page")
        this.render("pager")

        this.emit("datatable.page", page)
    }

    /**
     * Sort by column
     * @param  {int} column - The column no.
     * @param  {string} direction - asc or desc
     * @return {void}
     */
    sortColumn(column, direction) {
        // Use columns API until sortColumn method is removed
        this.columns().sort(column, direction)
    }

    /**
     * Add new row data
     * @param {object} data
     */
    insert(data) {
        let rows = []
        if ((0,_helpers__WEBPACK_IMPORTED_MODULE_4__.isObject)(data)) {
            if (data.headings) {
                if (!this.hasHeadings && !this.hasRows) {
                    const tr = (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.createElement)("tr")
                    data.headings.forEach(heading => {
                        const th = (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.createElement)("th", {
                            html: heading
                        })

                        tr.appendChild(th)
                    })
                    this.head.appendChild(tr)

                    this.header = tr
                    this.headings = [].slice.call(tr.cells)
                    this.hasHeadings = true

                    // Re-enable sorting if it was disabled due
                    // to missing header
                    this.options.sortable = this.initialSortable

                    // Allow sorting on new header
                    this.render("header")

                    // Activate newly added headings
                    this.activeHeadings = this.headings.slice()
                }
            }

            if (data.data && Array.isArray(data.data)) {
                rows = data.data
            }
        } else if (Array.isArray(data)) {
            data.forEach(row => {
                const r = []
                Object.entries(row).forEach(([heading, cell]) => {

                    const index = this.labels.indexOf(heading)

                    if (index > -1) {
                        r[index] = cell
                    }
                })
                rows.push(r)
            })
        }

        if (rows.length) {
            this.rows().add(rows)

            this.hasRows = true
        }

        this.update()
        this.setColumns()
        this.fixColumns()
    }

    /**
     * Refresh the instance
     * @return {void}
     */
    refresh() {
        if (this.options.searchable) {
            this.input.value = ""
            this.searching = false
        }
        this.currentPage = 1
        this.onFirstPage = true
        this.update()

        this.emit("datatable.refresh")
    }

    /**
     * Truncate the table
     * @param  {mixes} html - HTML string or HTMLElement
     * @return {void}
     */
    clear(html) {
        if (this.body) {
            (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.flush)(this.body)
        }

        let parent = this.body
        if (!this.body) {
            parent = this.table
        }

        if (html) {
            if (typeof html === "string") {
                const frag = document.createDocumentFragment()
                frag.innerHTML = html
            }

            parent.appendChild(html)
        }
    }

    /**
     * Export table to various formats (csv, txt or sql)
     * @param  {Object} userOptions User options
     * @return {Boolean}
     */
    export(userOptions) {
        if (!this.hasHeadings && !this.hasRows) return false

        const headers = this.activeHeadings
        let rows = []
        const arr = []
        let i
        let x
        let str
        let link

        const defaults = {
            download: true,
            skipColumn: [],

            // csv
            lineDelimiter: "\n",
            columnDelimiter: ",",

            // sql
            tableName: "myTable",

            // json
            replacer: null,
            space: 4
        }

        // Check for the options object
        if (!(0,_helpers__WEBPACK_IMPORTED_MODULE_4__.isObject)(userOptions)) {
            return false
        }

        const options = {
            ...defaults,
            ...userOptions
        }

        if (options.type) {
            if (options.type === "txt" || options.type === "csv") {
                // Include headings
                rows[0] = this.header
            }

            // Selection or whole table
            if (options.selection) {
                // Page number
                if (!isNaN(options.selection)) {
                    rows = rows.concat(this.pages[options.selection - 1])
                } else if (Array.isArray(options.selection)) {
                    // Array of page numbers
                    for (i = 0; i < options.selection.length; i++) {
                        rows = rows.concat(this.pages[options.selection[i] - 1])
                    }
                }
            } else {
                rows = rows.concat(this.activeRows)
            }

            // Only proceed if we have data
            if (rows.length) {
                if (options.type === "txt" || options.type === "csv") {
                    str = ""

                    for (i = 0; i < rows.length; i++) {
                        for (x = 0; x < rows[i].cells.length; x++) {
                            // Check for column skip and visibility
                            if (
                                !options.skipColumn.includes(headers[x].originalCellIndex) &&
                                this.columns(headers[x].originalCellIndex).visible()
                            ) {
                                let text = rows[i].cells[x].textContent
                                text = text.trim()
                                text = text.replace(/\s{2,}/g, ' ')
                                text = text.replace(/\n/g, '  ')
                                text = text.replace(/"/g, '""')
                                //have to manually encode "#" as encodeURI leaves it as is.
                                text = text.replace(/#/g, "%23")
                                if (text.includes(","))
                                    text = `"${text}"`


                                str += text + options.columnDelimiter
                            }
                        }
                        // Remove trailing column delimiter
                        str = str.trim().substring(0, str.length - 1)

                        // Apply line delimiter
                        str += options.lineDelimiter
                    }

                    // Remove trailing line delimiter
                    str = str.trim().substring(0, str.length - 1)

                    if (options.download) {
                        str = `data:text/csv;charset=utf-8,${str}`
                    }
                } else if (options.type === "sql") {
                    // Begin INSERT statement
                    str = `INSERT INTO \`${options.tableName}\` (`

                    // Convert table headings to column names
                    for (i = 0; i < headers.length; i++) {
                        // Check for column skip and column visibility
                        if (
                            !options.skipColumn.includes(headers[i].originalCellIndex) &&
                            this.columns(headers[i].originalCellIndex).visible()
                        ) {
                            str += `\`${headers[i].textContent}\`,`
                        }
                    }

                    // Remove trailing comma
                    str = str.trim().substring(0, str.length - 1)

                    // Begin VALUES
                    str += ") VALUES "

                    // Iterate rows and convert cell data to column values
                    for (i = 0; i < rows.length; i++) {
                        str += "("

                        for (x = 0; x < rows[i].cells.length; x++) {
                            // Check for column skip and column visibility
                            if (
                                !options.skipColumn.includes(headers[x].originalCellIndex) &&
                                this.columns(headers[x].originalCellIndex).visible()
                            ) {
                                str += `"${rows[i].cells[x].textContent}",`
                            }
                        }

                        // Remove trailing comma
                        str = str.trim().substring(0, str.length - 1)

                        // end VALUES
                        str += "),"
                    }

                    // Remove trailing comma
                    str = str.trim().substring(0, str.length - 1)

                    // Add trailing colon
                    str += ";"

                    if (options.download) {
                        str = `data:application/sql;charset=utf-8,${str}`
                    }
                } else if (options.type === "json") {
                    // Iterate rows
                    for (x = 0; x < rows.length; x++) {
                        arr[x] = arr[x] || {}
                        // Iterate columns
                        for (i = 0; i < headers.length; i++) {
                            // Check for column skip and column visibility
                            if (
                                !options.skipColumn.includes(headers[i].originalCellIndex) &&
                                this.columns(headers[i].originalCellIndex).visible()
                            ) {
                                arr[x][headers[i].textContent] = rows[x].cells[i].textContent
                            }
                        }
                    }

                    // Convert the array of objects to JSON string
                    str = JSON.stringify(arr, options.replacer, options.space)

                    if (options.download) {
                        str = `data:application/json;charset=utf-8,${str}`
                    }
                }

                // Download
                if (options.download) {
                    // Filename
                    options.filename = options.filename || "datatable_export"
                    options.filename += `.${options.type}`

                    str = encodeURI(str)

                    // Create a link to trigger the download
                    link = document.createElement("a")
                    link.href = str
                    link.download = options.filename

                    // Append the link
                    document.body.appendChild(link)

                    // Trigger the download
                    link.click()

                    // Remove the link
                    document.body.removeChild(link)
                }

                return str
            }
        }

        return false
    }

    /**
     * Import data to the table
     * @param  {Object} userOptions User options
     * @return {Boolean}
     */
    import(userOptions) {
        let obj = false
        const defaults = {
            // csv
            lineDelimiter: "\n",
            columnDelimiter: ","
        }

        // Check for the options object
        if (!(0,_helpers__WEBPACK_IMPORTED_MODULE_4__.isObject)(userOptions)) {
            return false
        }

        const options = {
            ...defaults,
            ...userOptions
        }

        if (options.data.length || (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.isObject)(options.data)) {
            // Import CSV
            if (options.type === "csv") {
                obj = {
                    data: []
                }

                // Split the string into rows
                const rows = options.data.split(options.lineDelimiter)

                if (rows.length) {

                    if (options.headings) {
                        obj.headings = rows[0].split(options.columnDelimiter)

                        rows.shift()
                    }

                    rows.forEach((row, i) => {
                        obj.data[i] = []

                        // Split the rows into values
                        const values = row.split(options.columnDelimiter)

                        if (values.length) {
                            values.forEach(value => {
                                obj.data[i].push(value)
                            })
                        }
                    })
                }
            } else if (options.type === "json") {
                const json = (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.isJson)(options.data)

                // Valid JSON string
                if (json) {
                    obj = {
                        headings: [],
                        data: []
                    }

                    json.forEach((data, i) => {
                        obj.data[i] = []
                        Object.entries(data).forEach(([column, value]) => {
                            if (!obj.headings.includes(column)) {
                                obj.headings.push(column)
                            }

                            obj.data[i].push(value)
                        })
                    })
                } else {
                    // console.warn("That's not valid JSON!")
                }
            }

            if ((0,_helpers__WEBPACK_IMPORTED_MODULE_4__.isObject)(options.data)) {
                obj = options.data
            }

            if (obj) {
                // Add the rows
                this.insert(obj)
            }
        }

        return false
    }

    /**
     * Print the table
     * @return {void}
     */
    print() {
        const headings = this.activeHeadings
        const rows = this.activeRows
        const table = (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.createElement)("table")
        const thead = (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.createElement)("thead")
        const tbody = (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.createElement)("tbody")

        const tr = (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.createElement)("tr")
        headings.forEach(th => {
            tr.appendChild(
                (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.createElement)("th", {
                    html: th.textContent
                })
            )
        })

        thead.appendChild(tr)

        rows.forEach(row => {
            const tr = (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.createElement)("tr")
            Array.from(row.cells).forEach(cell => {
                tr.appendChild(
                    (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.createElement)("td", {
                        html: cell.textContent
                    })
                )
            })
            tbody.appendChild(tr)
        })

        table.appendChild(thead)
        table.appendChild(tbody)

        // Open new window
        const w = window.open()

        // Append the table to the body
        w.document.body.appendChild(table)

        // Print
        w.print()
    }

    /**
     * Show a message in the table
     * @param {string} message
     */
    setMessage(message) {
        let colspan = 1

        if (this.hasRows) {
            colspan = this.data[0].cells.length
        } else if (this.activeHeadings.length) {
            colspan = this.activeHeadings.length
        }

        this.wrapper.classList.add("dataTable-empty")

        if (this.label) {
            this.label.innerHTML = ""
        }
        this.totalPages = 0
        this.render("pager")

        this.clear(
            (0,_helpers__WEBPACK_IMPORTED_MODULE_4__.createElement)("tr", {
                html: `<td class="dataTables-empty" colspan="${colspan}">${message}</td>`
            })
        )
    }

    /**
     * Columns API access
     * @return {Object} new Columns instance
     */
    columns(columns) {
        return new _columns__WEBPACK_IMPORTED_MODULE_1__.Columns(this, columns)
    }

    /**
     * Rows API access
     * @return {Object} new Rows instance
     */
    rows(rows) {
        return new _rows__WEBPACK_IMPORTED_MODULE_0__.Rows(this, rows)
    }

    /**
     * Add custom event listener
     * @param  {String} event
     * @param  {Function} callback
     * @return {Void}
     */
    on(event, callback) {
        this.events = this.events || {}
        this.events[event] = this.events[event] || []
        this.events[event].push(callback)
    }

    /**
     * Remove custom event listener
     * @param  {String} event
     * @param  {Function} callback
     * @return {Void}
     */
    off(event, callback) {
        this.events = this.events || {}
        if (event in this.events === false) return
        this.events[event].splice(this.events[event].indexOf(callback), 1)
    }

    /**
     * Fire custom event
     * @param  {String} event
     * @return {Void}
     */
    emit(event) {
        this.events = this.events || {}
        if (event in this.events === false) return
        for (let i = 0; i < this.events[event].length; i++) {
            this.events[event][i].apply(this, Array.prototype.slice.call(arguments, 1))
        }
    }
}


/***/ }),

/***/ "./node_modules/simple-datatables/src/helpers.js":
/*!*******************************************************!*\
  !*** ./node_modules/simple-datatables/src/helpers.js ***!
  \*******************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "button": () => (/* binding */ button),
/* harmony export */   "createElement": () => (/* binding */ createElement),
/* harmony export */   "flush": () => (/* binding */ flush),
/* harmony export */   "isJson": () => (/* binding */ isJson),
/* harmony export */   "isObject": () => (/* binding */ isObject),
/* harmony export */   "sortItems": () => (/* binding */ sortItems),
/* harmony export */   "truncate": () => (/* binding */ truncate)
/* harmony export */ });
/**
 * Check is item is object
 * @return {Boolean}
 */
const isObject = val => Object.prototype.toString.call(val) === "[object Object]"

/**
 * Check for valid JSON string
 * @param  {String}   str
 * @return {Boolean|Array|Object}
 */
const isJson = str => {
    let t = !1
    try {
        t = JSON.parse(str)
    } catch (e) {
        return !1
    }
    return !(null === t || (!Array.isArray(t) && !isObject(t))) && t
}

/**
 * Create DOM element node
 * @param  {String}   nodeName nodeName
 * @param  {Object}   attrs properties and attributes
 * @return {Object}
 */
const createElement = (nodeName, attrs) => {
    const dom = document.createElement(nodeName)
    if (attrs && "object" == typeof attrs) {
        for (const attr in attrs) {
            if ("html" === attr) {
                dom.innerHTML = attrs[attr]
            } else {
                dom.setAttribute(attr, attrs[attr])
            }
        }
    }
    return dom
}

const flush = el => {
    if (el instanceof NodeList) {
        el.forEach(e => flush(e))
    } else {
        el.innerHTML = ""
    }
}

/**
 * Create button helper
 * @param  {String}   class
 * @param  {Number}   page
 * @param  {String}   text
 * @return {Object}
 */
const button = (className, page, text) => createElement(
    "li",
    {
        class: className,
        html: `<a href="#" data-page="${page}">${text}</a>`
    }
)

/**
 * Bubble sort algorithm
 */
const sortItems = (a, b) => {
    let c
    let d
    if (1 === b) {
        c = 0
        d = a.length
    } else {
        if (b === -1) {
            c = a.length - 1
            d = -1
        }
    }
    for (let e = !0; e;) {
        e = !1
        for (let f = c; f != d; f += b) {
            if (a[f + b] && a[f].value > a[f + b].value) {
                const g = a[f]
                const h = a[f + b]
                const i = g
                a[f] = h
                a[f + b] = i
                e = !0
            }
        }
    }
    return a
}

/**
 * Pager truncation algorithm
 */
const truncate = (a, b, c, d, ellipsis) => {
    d = d || 2
    let j
    const e = 2 * d
    let f = b - d
    let g = b + d
    const h = []
    const i = []
    if (b < 4 - d + e) {
        g = 3 + e
    } else if (b > c - (3 - d + e)) {
        f = c - (2 + e)
    }
    for (let k = 1; k <= c; k++) {
        if (1 == k || k == c || (k >= f && k <= g)) {
            const l = a[k - 1]
            l.classList.remove("active")
            h.push(l)
        }
    }
    h.forEach(c => {
        const d = c.children[0].getAttribute("data-page")
        if (j) {
            const e = j.children[0].getAttribute("data-page")
            if (d - e == 2) i.push(a[e])
            else if (d - e != 1) {
                const f = createElement("li", {
                    class: "ellipsis",
                    html: `<a href="#">${ellipsis}</a>`
                })
                i.push(f)
            }
        }
        i.push(c)
        j = c
    })

    return i
}


/***/ }),

/***/ "./node_modules/simple-datatables/src/index.js":
/*!*****************************************************!*\
  !*** ./node_modules/simple-datatables/src/index.js ***!
  \*****************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "DataTable": () => (/* reexport safe */ _datatable__WEBPACK_IMPORTED_MODULE_0__.DataTable)
/* harmony export */ });
/* harmony import */ var _datatable__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./datatable */ "./node_modules/simple-datatables/src/datatable.js");
/*!
 *
 * Simple-DataTables
 * Copyright (c) 2015-2017 Karl Saunders (https://mobius.ovh)
 * Copyright (c) 2018- Johannes Wilm (https://www.johanneswilm.org)
 * Licensed under MIT (https://www.opensource.org/licenses/mit-license.php)
 *
 *
 */




/***/ }),

/***/ "./node_modules/simple-datatables/src/rows.js":
/*!****************************************************!*\
  !*** ./node_modules/simple-datatables/src/rows.js ***!
  \****************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "Rows": () => (/* binding */ Rows)
/* harmony export */ });
/* harmony import */ var _helpers__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./helpers */ "./node_modules/simple-datatables/src/helpers.js");

/**
 * Rows API
 * @param {Object} instance DataTable instance
 * @param {Array} rows
 */
class Rows {
    constructor(dt, rows) {
        this.dt = dt
        this.rows = rows

        return this
    }

    /**
     * Build a new row
     * @param  {Array} row
     * @return {HTMLElement}
     */
    build(row) {
        const tr = (0,_helpers__WEBPACK_IMPORTED_MODULE_0__.createElement)("tr")

        let headings = this.dt.headings

        if (!headings.length) {
            headings = row.map(() => "")
        }

        headings.forEach((h, i) => {
            const td = (0,_helpers__WEBPACK_IMPORTED_MODULE_0__.createElement)("td")

            // Fixes #29
            if (!row[i] || !row[i].length) {
                row[i] = ""
            }

            td.innerHTML = row[i]

            td.data = row[i]

            tr.appendChild(td)
        })

        return tr
    }

    render(row) {
        return row
    }

    /**
     * Add new row
     * @param {Array} select
     */
    add(data) {
        if (Array.isArray(data)) {
            const dt = this.dt
            // Check for multiple rows
            if (Array.isArray(data[0])) {
                data.forEach(row => {
                    dt.data.push(this.build(row))
                })
            } else {
                dt.data.push(this.build(data))
            }

            // We may have added data to an empty table
            if ( dt.data.length ) {
                dt.hasRows = true
            }


            this.update()

            dt.columns().rebuild()
        }

    }

    /**
     * Remove row(s)
     * @param  {Array|Number} select
     * @return {Void}
     */
    remove(select) {
        const dt = this.dt

        if (Array.isArray(select)) {
            // Remove in reverse otherwise the indexes will be incorrect
            select.sort((a, b) => b - a)

            select.forEach(row => {
                dt.data.splice(row, 1)
            })
        } else if (select == 'all') {
            dt.data = [];
        } else {
            dt.data.splice(select, 1)
        }

        // We may have emptied the table
        if ( !dt.data.length ) {
            dt.hasRows = false
        }

        this.update()
        dt.columns().rebuild()
    }

    /**
     * Update row indexes
     * @return {Void}
     */
    update() {
        this.dt.data.forEach((row, i) => {
            row.dataIndex = i
        })
    }
}


/***/ }),

/***/ "./node_modules/simple-datatables/src/table.js":
/*!*****************************************************!*\
  !*** ./node_modules/simple-datatables/src/table.js ***!
  \*****************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "dataToTable": () => (/* binding */ dataToTable)
/* harmony export */ });
/* harmony import */ var _helpers__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./helpers */ "./node_modules/simple-datatables/src/helpers.js");


/**
 * Parse data to HTML table
 */
const dataToTable = function (data) {
    let thead = false
    let tbody = false

    data = data || this.options.data

    if (data.headings) {
        thead = (0,_helpers__WEBPACK_IMPORTED_MODULE_0__.createElement)("thead")
        const tr = (0,_helpers__WEBPACK_IMPORTED_MODULE_0__.createElement)("tr")
        data.headings.forEach(col => {
            const td = (0,_helpers__WEBPACK_IMPORTED_MODULE_0__.createElement)("th", {
                html: col
            })
            tr.appendChild(td)
        })

        thead.appendChild(tr)
    }

    if (data.data && data.data.length) {
        tbody = (0,_helpers__WEBPACK_IMPORTED_MODULE_0__.createElement)("tbody")
        data.data.forEach(rows => {
            if (data.headings) {
                if (data.headings.length !== rows.length) {
                    throw new Error(
                        "The number of rows do not match the number of headings."
                    )
                }
            }
            const tr = (0,_helpers__WEBPACK_IMPORTED_MODULE_0__.createElement)("tr")
            rows.forEach(value => {
                const td = (0,_helpers__WEBPACK_IMPORTED_MODULE_0__.createElement)("td", {
                    html: value
                })
                tr.appendChild(td)
            })
            tbody.appendChild(tr)
        })
    }

    if (thead) {
        if (this.table.tHead !== null) {
            this.table.removeChild(this.table.tHead)
        }
        this.table.appendChild(thead)
    }

    if (tbody) {
        if (this.table.tBodies.length) {
            this.table.removeChild(this.table.tBodies[0])
        }
        this.table.appendChild(tbody)
    }
}


/***/ })

/******/ 	});
/************************************************************************/
/******/ 	// The module cache
/******/ 	var __webpack_module_cache__ = {};
/******/ 	
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/ 		// Check if module is in cache
/******/ 		var cachedModule = __webpack_module_cache__[moduleId];
/******/ 		if (cachedModule !== undefined) {
/******/ 			return cachedModule.exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = __webpack_module_cache__[moduleId] = {
/******/ 			// no module.id needed
/******/ 			// no module.loaded needed
/******/ 			exports: {}
/******/ 		};
/******/ 	
/******/ 		// Execute the module function
/******/ 		__webpack_modules__[moduleId].call(module.exports, module, module.exports, __webpack_require__);
/******/ 	
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/ 	
/******/ 	// expose the modules object (__webpack_modules__)
/******/ 	__webpack_require__.m = __webpack_modules__;
/******/ 	
/************************************************************************/
/******/ 	/* webpack/runtime/compat get default export */
/******/ 	(() => {
/******/ 		// getDefaultExport function for compatibility with non-harmony modules
/******/ 		__webpack_require__.n = (module) => {
/******/ 			var getter = module && module.__esModule ?
/******/ 				() => (module['default']) :
/******/ 				() => (module);
/******/ 			__webpack_require__.d(getter, { a: getter });
/******/ 			return getter;
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/define property getters */
/******/ 	(() => {
/******/ 		// define getter functions for harmony exports
/******/ 		__webpack_require__.d = (exports, definition) => {
/******/ 			for(var key in definition) {
/******/ 				if(__webpack_require__.o(definition, key) && !__webpack_require__.o(exports, key)) {
/******/ 					Object.defineProperty(exports, key, { enumerable: true, get: definition[key] });
/******/ 				}
/******/ 			}
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/ensure chunk */
/******/ 	(() => {
/******/ 		__webpack_require__.f = {};
/******/ 		// This file contains only the entry chunk.
/******/ 		// The chunk loading function for additional chunks
/******/ 		__webpack_require__.e = (chunkId) => {
/******/ 			return Promise.all(Object.keys(__webpack_require__.f).reduce((promises, key) => {
/******/ 				__webpack_require__.f[key](chunkId, promises);
/******/ 				return promises;
/******/ 			}, []));
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/get javascript chunk filename */
/******/ 	(() => {
/******/ 		// This function allow to reference async chunks
/******/ 		__webpack_require__.u = (chunkId) => {
/******/ 			// return url for filenames not based on template
/******/ 			if (chunkId === "node_modules_simple-datatables_src_date_js") return "assets/js/" + chunkId + ".js";
/******/ 			// return url for filenames based on template
/******/ 			return undefined;
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/get mini-css chunk filename */
/******/ 	(() => {
/******/ 		// This function allow to reference all chunks
/******/ 		__webpack_require__.miniCssF = (chunkId) => {
/******/ 			// return url for filenames based on template
/******/ 			return undefined;
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/hasOwnProperty shorthand */
/******/ 	(() => {
/******/ 		__webpack_require__.o = (obj, prop) => (Object.prototype.hasOwnProperty.call(obj, prop))
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/load script */
/******/ 	(() => {
/******/ 		var inProgress = {};
/******/ 		var dataWebpackPrefix = "mazer:";
/******/ 		// loadScript function to load a script via script tag
/******/ 		__webpack_require__.l = (url, done, key, chunkId) => {
/******/ 			if(inProgress[url]) { inProgress[url].push(done); return; }
/******/ 			var script, needAttach;
/******/ 			if(key !== undefined) {
/******/ 				var scripts = document.getElementsByTagName("script");
/******/ 				for(var i = 0; i < scripts.length; i++) {
/******/ 					var s = scripts[i];
/******/ 					if(s.getAttribute("src") == url || s.getAttribute("data-webpack") == dataWebpackPrefix + key) { script = s; break; }
/******/ 				}
/******/ 			}
/******/ 			if(!script) {
/******/ 				needAttach = true;
/******/ 				script = document.createElement('script');
/******/ 		
/******/ 				script.charset = 'utf-8';
/******/ 				script.timeout = 120;
/******/ 				if (__webpack_require__.nc) {
/******/ 					script.setAttribute("nonce", __webpack_require__.nc);
/******/ 				}
/******/ 				script.setAttribute("data-webpack", dataWebpackPrefix + key);
/******/ 				script.src = url;
/******/ 			}
/******/ 			inProgress[url] = [done];
/******/ 			var onScriptComplete = (prev, event) => {
/******/ 				// avoid mem leaks in IE.
/******/ 				script.onerror = script.onload = null;
/******/ 				clearTimeout(timeout);
/******/ 				var doneFns = inProgress[url];
/******/ 				delete inProgress[url];
/******/ 				script.parentNode && script.parentNode.removeChild(script);
/******/ 				doneFns && doneFns.forEach((fn) => (fn(event)));
/******/ 				if(prev) return prev(event);
/******/ 			}
/******/ 			;
/******/ 			var timeout = setTimeout(onScriptComplete.bind(null, undefined, { type: 'timeout', target: script }), 120000);
/******/ 			script.onerror = onScriptComplete.bind(null, script.onerror);
/******/ 			script.onload = onScriptComplete.bind(null, script.onload);
/******/ 			needAttach && document.head.appendChild(script);
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/make namespace object */
/******/ 	(() => {
/******/ 		// define __esModule on exports
/******/ 		__webpack_require__.r = (exports) => {
/******/ 			if(typeof Symbol !== 'undefined' && Symbol.toStringTag) {
/******/ 				Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' });
/******/ 			}
/******/ 			Object.defineProperty(exports, '__esModule', { value: true });
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/publicPath */
/******/ 	(() => {
/******/ 		__webpack_require__.p = "/";
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/jsonp chunk loading */
/******/ 	(() => {
/******/ 		// no baseURI
/******/ 		
/******/ 		// object to store loaded and loading chunks
/******/ 		// undefined = chunk not loaded, null = chunk preloaded/prefetched
/******/ 		// [resolve, reject, Promise] = chunk loading, 0 = chunk loaded
/******/ 		var installedChunks = {
/******/ 			"/assets/js/extensions/simple-datatables": 0
/******/ 		};
/******/ 		
/******/ 		__webpack_require__.f.j = (chunkId, promises) => {
/******/ 				// JSONP chunk loading for javascript
/******/ 				var installedChunkData = __webpack_require__.o(installedChunks, chunkId) ? installedChunks[chunkId] : undefined;
/******/ 				if(installedChunkData !== 0) { // 0 means "already installed".
/******/ 		
/******/ 					// a Promise means "currently loading".
/******/ 					if(installedChunkData) {
/******/ 						promises.push(installedChunkData[2]);
/******/ 					} else {
/******/ 						if(true) { // all chunks have JS
/******/ 							// setup Promise in chunk cache
/******/ 							var promise = new Promise((resolve, reject) => (installedChunkData = installedChunks[chunkId] = [resolve, reject]));
/******/ 							promises.push(installedChunkData[2] = promise);
/******/ 		
/******/ 							// start chunk loading
/******/ 							var url = __webpack_require__.p + __webpack_require__.u(chunkId);
/******/ 							// create error before stack unwound to get useful stacktrace later
/******/ 							var error = new Error();
/******/ 							var loadingEnded = (event) => {
/******/ 								if(__webpack_require__.o(installedChunks, chunkId)) {
/******/ 									installedChunkData = installedChunks[chunkId];
/******/ 									if(installedChunkData !== 0) installedChunks[chunkId] = undefined;
/******/ 									if(installedChunkData) {
/******/ 										var errorType = event && (event.type === 'load' ? 'missing' : event.type);
/******/ 										var realSrc = event && event.target && event.target.src;
/******/ 										error.message = 'Loading chunk ' + chunkId + ' failed.\n(' + errorType + ': ' + realSrc + ')';
/******/ 										error.name = 'ChunkLoadError';
/******/ 										error.type = errorType;
/******/ 										error.request = realSrc;
/******/ 										installedChunkData[1](error);
/******/ 									}
/******/ 								}
/******/ 							};
/******/ 							__webpack_require__.l(url, loadingEnded, "chunk-" + chunkId, chunkId);
/******/ 						} else installedChunks[chunkId] = 0;
/******/ 					}
/******/ 				}
/******/ 		};
/******/ 		
/******/ 		// no prefetching
/******/ 		
/******/ 		// no preloaded
/******/ 		
/******/ 		// no HMR
/******/ 		
/******/ 		// no HMR manifest
/******/ 		
/******/ 		// no on chunks loaded
/******/ 		
/******/ 		// install a JSONP callback for chunk loading
/******/ 		var webpackJsonpCallback = (parentChunkLoadingFunction, data) => {
/******/ 			var [chunkIds, moreModules, runtime] = data;
/******/ 			// add "moreModules" to the modules object,
/******/ 			// then flag all "chunkIds" as loaded and fire callback
/******/ 			var moduleId, chunkId, i = 0;
/******/ 			if(chunkIds.some((id) => (installedChunks[id] !== 0))) {
/******/ 				for(moduleId in moreModules) {
/******/ 					if(__webpack_require__.o(moreModules, moduleId)) {
/******/ 						__webpack_require__.m[moduleId] = moreModules[moduleId];
/******/ 					}
/******/ 				}
/******/ 				if(runtime) var result = runtime(__webpack_require__);
/******/ 			}
/******/ 			if(parentChunkLoadingFunction) parentChunkLoadingFunction(data);
/******/ 			for(;i < chunkIds.length; i++) {
/******/ 				chunkId = chunkIds[i];
/******/ 				if(__webpack_require__.o(installedChunks, chunkId) && installedChunks[chunkId]) {
/******/ 					installedChunks[chunkId][0]();
/******/ 				}
/******/ 				installedChunks[chunkId] = 0;
/******/ 			}
/******/ 		
/******/ 		}
/******/ 		
/******/ 		var chunkLoadingGlobal = self["webpackChunkmazer"] = self["webpackChunkmazer"] || [];
/******/ 		chunkLoadingGlobal.forEach(webpackJsonpCallback.bind(null, 0));
/******/ 		chunkLoadingGlobal.push = webpackJsonpCallback.bind(null, chunkLoadingGlobal.push.bind(chunkLoadingGlobal));
/******/ 	})();
/******/ 	
/************************************************************************/
var __webpack_exports__ = {};
// This entry need to be wrapped in an IIFE because it need to be isolated against other modules in the chunk.
(() => {
/*!*******************************************************!*\
  !*** ./src/assets/js/extensions/simple-datatables.js ***!
  \*******************************************************/
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var simple_datatables__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! simple-datatables */ "./node_modules/simple-datatables/src/index.js");
function _createForOfIteratorHelper(o, allowArrayLike) { var it = typeof Symbol !== "undefined" && o[Symbol.iterator] || o["@@iterator"]; if (!it) { if (Array.isArray(o) || (it = _unsupportedIterableToArray(o)) || allowArrayLike && o && typeof o.length === "number") { if (it) o = it; var i = 0; var F = function F() {}; return { s: F, n: function n() { if (i >= o.length) return { done: true }; return { done: false, value: o[i++] }; }, e: function e(_e) { throw _e; }, f: F }; } throw new TypeError("Invalid attempt to iterate non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); } var normalCompletion = true, didErr = false, err; return { s: function s() { it = it.call(o); }, n: function n() { var step = it.next(); normalCompletion = step.done; return step; }, e: function e(_e2) { didErr = true; err = _e2; }, f: function f() { try { if (!normalCompletion && it["return"] != null) it["return"](); } finally { if (didErr) throw err; } } }; }

function _unsupportedIterableToArray(o, minLen) { if (!o) return; if (typeof o === "string") return _arrayLikeToArray(o, minLen); var n = Object.prototype.toString.call(o).slice(8, -1); if (n === "Object" && o.constructor) n = o.constructor.name; if (n === "Map" || n === "Set") return Array.from(o); if (n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)) return _arrayLikeToArray(o, minLen); }

function _arrayLikeToArray(arr, len) { if (len == null || len > arr.length) len = arr.length; for (var i = 0, arr2 = new Array(len); i < len; i++) { arr2[i] = arr[i]; } return arr2; }


var dataTable = new simple_datatables__WEBPACK_IMPORTED_MODULE_0__.DataTable(document.getElementById("table1")); // Move "per page dropdown" selector element out of label
// to make it work with bootstrap 5. Add bs5 classes.

function adaptPageDropdown() {
  var selector = dataTable.wrapper.querySelector(".dataTable-selector");
  selector.parentNode.parentNode.insertBefore(selector, selector.parentNode);
  selector.classList.add("form-select");
} // Add bs5 classes to pagination elements


function adaptPagination() {
  var paginations = dataTable.wrapper.querySelectorAll("ul.dataTable-pagination-list");

  var _iterator = _createForOfIteratorHelper(paginations),
      _step;

  try {
    for (_iterator.s(); !(_step = _iterator.n()).done;) {
      var _pagination$classList;

      var pagination = _step.value;

      (_pagination$classList = pagination.classList).add.apply(_pagination$classList, ["pagination", "pagination-primary"]);
    }
  } catch (err) {
    _iterator.e(err);
  } finally {
    _iterator.f();
  }

  var paginationLis = dataTable.wrapper.querySelectorAll("ul.dataTable-pagination-list li");

  var _iterator2 = _createForOfIteratorHelper(paginationLis),
      _step2;

  try {
    for (_iterator2.s(); !(_step2 = _iterator2.n()).done;) {
      var paginationLi = _step2.value;
      paginationLi.classList.add("page-item");
    }
  } catch (err) {
    _iterator2.e(err);
  } finally {
    _iterator2.f();
  }

  var paginationLinks = dataTable.wrapper.querySelectorAll("ul.dataTable-pagination-list li a");

  var _iterator3 = _createForOfIteratorHelper(paginationLinks),
      _step3;

  try {
    for (_iterator3.s(); !(_step3 = _iterator3.n()).done;) {
      var paginationLink = _step3.value;
      paginationLink.classList.add("page-link");
    }
  } catch (err) {
    _iterator3.e(err);
  } finally {
    _iterator3.f();
  }
} // Patch "per page dropdown" and pagination after table rendered


dataTable.on("datatable.init", function () {
  adaptPageDropdown();
  adaptPagination();
}); // Re-patch pagination after the page was changed

dataTable.on("datatable.page", adaptPagination);
})();

/******/ })()
;