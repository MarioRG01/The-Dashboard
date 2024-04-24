import { Component, inject, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { IonHeader, IonToolbar, IonButtons, IonMenuButton, IonTitle, IonContent, IonIcon, IonButton, IonDatetimeButton, IonModal, IonDatetime, IonRadio, IonRadioGroup } from '@ionic/angular/standalone';
import { NgxChartsModule } from '@swimlane/ngx-charts';
import { DayLifeTimePickerComponent } from '../day-life-time-picker/day-life-time-picker.component';
import { NgIf } from '@angular/common';
import { PieChartGraphicComponent } from '../pie-chart-graphic/pie-chart-graphic.component';
import { FactorySimDataService } from '../factory-sim-data.service';
import { BarChartGraphicComponent } from '../bar-chart-graphic/bar-chart-graphic.component';

@Component({
  selector: 'app-folder',
  templateUrl: './folder.page.html',
  styleUrls: ['./folder.page.scss'],
  standalone: true,
  imports: [IonButton, IonHeader, IonToolbar, IonButtons, IonMenuButton, IonTitle, IonContent, DayLifeTimePickerComponent, BarChartGraphicComponent, PieChartGraphicComponent, IonIcon, IonDatetimeButton, IonModal, IonDatetime, NgIf, IonRadio, IonRadioGroup],
})
export class FolderPage implements OnInit {
  public folder!: string;
  private activatedRoute = inject(ActivatedRoute);
  timePeriod: string = 'day'
  periodDate1: string = ''
  periodDate2: string = ''
  minDate: string = new Date().toISOString()
  maxDate: string = new Date().toISOString()
  todayDate: Date = new Date()
  today: string = this.getTodayDate();
  lastDay: string = "23/04/2025"
  dailyData: any = {}
  selectedDates = {
    'day': this.formatDate(this.minDate),
    'week': {day1: this.formatDate(this.minDate), day2: this.getCustomDaysDate(new Date(this.minDate), 6)},
    'month': {"month": this.formatDate(this.minDate).split("/")[1], "year":this.formatDate(this.minDate).split("/")[2]},
    'quarter': {"q": this.getQuarter(this.formatDate(this.minDate)), "year":this.formatDate(this.minDate).split("/")[2]},
    'year': this.formatDate(this.minDate).split("/")[2],
    'all': {day1: this.formatDate(this.minDate), day2: this.formatDate(this.maxDate)},
    'custom': {day1: this.formatDate(this.minDate), day2: this.getCustomDaysDate(new Date(this.minDate), 1)}
  }
  selectedDay: string = this.formatDate(this.today)
  constructor(private factorySimDataService: FactorySimDataService) {}

  ngOnInit() {
    this.folder = this.activatedRoute.snapshot.paramMap.get('id') as string;
    if(!this.factorySimDataService.dataFetched) {
      this.fetchAllData();
    }else {
      this.dailyData = this.factorySimDataService.getDailyProduction();
      this.minDate = this.getMinDate();
      this.maxDate = this.getMaxDate();
      this.selectedDates = {
        'day': this.formatDate(this.minDate),
        'week': {day1: this.formatDate(this.minDate), day2: this.getCustomDaysDate(new Date(this.minDate), 6)},
        'month': {"month": this.formatDate(this.minDate).split("/")[1], "year":this.formatDate(this.minDate).split("/")[2]},
        'quarter': {"q": this.getQuarter(this.formatDate(this.minDate)), "year":this.formatDate(this.minDate).split("/")[2]},
        'year': this.formatDate(this.minDate).split("/")[2],
        'all': {day1: this.formatDate(this.minDate), day2: this.formatDate(this.maxDate)},
        'custom': {day1: this.formatDate(this.minDate), day2: this.getCustomDaysDate(new Date(this.minDate), 1)}
      }
    }
  }

  getDaysDate(days: any) {
    const today = new Date();
    const tomorrow = new Date(today.getTime() + 24 * 60 * 60 * 1000 * days);
    const formattedDate = tomorrow.toLocaleDateString('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
    return formattedDate;
  }

  getCustomDaysDate(date: Date, days: any) {
    const today = date;
    const tomorrow = new Date(today.getTime() + 24 * 60 * 60 * 1000 * days);
    const formattedDate = tomorrow.toLocaleDateString('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
    return formattedDate;
  }

  getCustomMinusDaysDate(date: Date, days: any) {
    const today = date;
    const tomorrow = new Date(today.getTime() - 24 * 60 * 60 * 1000 * days);
    const formattedDate = tomorrow.toLocaleDateString('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
    return formattedDate;
  }

  onDayChange(event: any) {
    let dateString: string = (event.detail.value)
    console.log("datestring", dateString)
    if(dateString.includes("T")){
      dateString = dateString.split('T')[0]
    }
    const formattedDate = dateString.split("-")[2] + '/' + dateString.split("-")[1] + '/' + dateString.split("-")[0]
    this.selectedDates["day"] = formattedDate;
    this.periodDate1 = formattedDate
    console.log("buscp", this.periodDate1)
    this.periodDate2 = formattedDate
  }

  onWeek1Change(event: any) {
    let dateString: string = event.detail.value
    const date = new Date(dateString);

    console.log("datestring", dateString)
    if(dateString.includes("T")){
      dateString = dateString.split('T')[0]
    }
    const formattedDate = dateString.split("-")[2] + '/' + dateString.split("-")[1] + '/' + dateString.split("-")[0]

    this.selectedDates['week'].day1 = formattedDate;

    const week2Date = new Date(date.getTime() + 24 * 60 * 60 * 1000 * 7);
    const formattedDate2 = week2Date.toLocaleDateString('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
    this.selectedDates['week'].day2 = formattedDate2;

    this.periodDate1 = (this.selectedDates[this.timePeriod as keyof typeof this.selectedDates] as {day1: string}).day1
    this.periodDate2 = (this.selectedDates[this.timePeriod as keyof typeof this.selectedDates] as {day2: string}).day2

  }

  onWeek2Change(event: any) {
    let dateString: string = event.detail.value;
    const date = new Date(dateString);
    console.log("datestring", dateString)
    if(dateString.includes("T")){
      dateString = dateString.split('T')[0]
    }
    const formattedDate = dateString.split("-")[2] + '/' + dateString.split("-")[1] + '/' + dateString.split("-")[0]
    this.selectedDates['week'].day2 = formattedDate;

    const week1Date = new Date(date.getTime() - 24 * 60 * 60 * 1000 * 5);
    const formattedDate2 = week1Date.toLocaleDateString('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
    this.selectedDates['week'].day1 = formattedDate2;

    this.periodDate1 = (this.selectedDates[this.timePeriod as keyof typeof this.selectedDates] as {day1: string}).day1
    this.periodDate2 = (this.selectedDates[this.timePeriod as keyof typeof this.selectedDates] as {day2: string}).day2
  }

  onMonthChange(event: any) {
    let dateString: string = (event.detail.value)
    console.log("datestring", dateString)
    if(dateString.includes("T")){
      dateString = dateString.split('T')[0]
    }
    const formattedDate = dateString.split("-")[2] + '/' + dateString.split("-")[1] + '/' + dateString.split("-")[0]
    this.selectedDates['month'].month = formattedDate.split("/")[1];
    this.selectedDates['month'].year = formattedDate.split("/")[2];

    this.periodDate1 = '01/' + this.selectedDates['month'].month + '/' + this.selectedDates['month'].year
    this.periodDate2 = '01/' + (parseInt(this.selectedDates['month'].month)+1).toString() + '/' + this.selectedDates['month'].year
    console.log("period dates month", this.periodDate1, this.periodDate2)
  }

  onQuarterNumChange(event: any) {
    const q = event.detail.value
    console.log(q)
    this.selectedDates['quarter'].q = parseInt(q[1]);

    if(q === 'q1'){
      this.periodDate1 = "01/01/"+this.selectedDates['quarter'].year
      this.periodDate2 = "01/04/"+this.selectedDates['quarter'].year
    }else if(q == 'q2'){
      this.periodDate1 = "01/04/"+this.selectedDates['quarter'].year
      this.periodDate2 = "01/07/"+this.selectedDates['quarter'].year
    }else if(q == 'q3'){
      this.periodDate1 = "01/07/"+this.selectedDates['quarter'].year
      this.periodDate2 = "01/10/"+this.selectedDates['quarter'].year
    }else if(q == 'q4'){
      this.periodDate1 = "01/10/"+this.selectedDates['quarter'].year
      this.periodDate2 = "31/12/"+this.selectedDates['quarter'].year
    }
  }

  onQuarterYearChange(event: any) {
    let dateString: string = (event.detail.value)
    console.log("datestring", dateString)
    if(dateString.includes("T")){
      dateString = dateString.split('T')[0]
    }
    const formattedDate = dateString.split("-")[2] + '/' + dateString.split("-")[1] + '/' + dateString.split("-")[0]
    this.selectedDates['quarter'].year = formattedDate.split("/")[2];

    const q = this.selectedDates['quarter'].q;

    if(q === 1){
      this.periodDate1 = "01/01/"+this.selectedDates['quarter'].year
      this.periodDate2 = "01/04/"+this.selectedDates['quarter'].year
    }else if(q == 2){
      this.periodDate1 = "01/04/"+this.selectedDates['quarter'].year
      this.periodDate2 = "01/07/"+this.selectedDates['quarter'].year
    }else if(q == 3){
      this.periodDate1 = "01/07/"+this.selectedDates['quarter'].year
      this.periodDate2 = "01/10/"+this.selectedDates['quarter'].year
    }else if(q == 4){
      this.periodDate1 = "01/10/"+this.selectedDates['quarter'].year
      this.periodDate2 = "31/12/"+this.selectedDates['quarter'].year
    }
  }

  onYearChange(event: any) {
    let dateString: string = (event.detail.value)
    console.log("datestring", dateString)
    if(dateString.includes("T")){
      dateString = dateString.split('T')[0]
    }
    const formattedDate = dateString.split("-")[2] + '/' + dateString.split("-")[1] + '/' + dateString.split("-")[0]
    this.selectedDates['year'] = formattedDate.split("/")[2];

    this.periodDate1 = "01/01/" + this.selectedDates['year']
    this.periodDate2 = "31/12/" + this.selectedDates['year']
    console.log("period dates year", this.periodDate1, this.periodDate2)
  }

  onCustomDate1Change(event: any) {
    let dateString: string = (event.detail.value)
    console.log("datestring", dateString)
    if(dateString.includes("T")){
      dateString = dateString.split('T')[0]
    }
    const formattedDate = dateString.split("-")[2] + '/' + dateString.split("-")[1] + '/' + dateString.split("-")[0]
    this.selectedDates["custom"].day1 = formattedDate;
    if(this.compareDate(this.selectedDates["custom"].day1, this.selectedDates["custom"].day2)) {
      this.selectedDates["custom"].day2 = this.selectedDates["custom"].day1
    }

    this.periodDate1 = (this.selectedDates[this.timePeriod as keyof typeof this.selectedDates] as {day1: string}).day1
    this.periodDate2 = (this.selectedDates[this.timePeriod as keyof typeof this.selectedDates] as {day2: string}).day2

  }

  onCustomDate2Change(event: any) {
    let dateString: string = (event.detail.value)
    console.log("datestring", dateString)
    if(dateString.includes("T")){
      dateString = dateString.split('T')[0]
    }
    const formattedDate = dateString.split("-")[2] + '/' + dateString.split("-")[1] + '/' + dateString.split("-")[0]
    this.selectedDates["custom"].day2 = formattedDate;

    this.periodDate2 = (this.selectedDates[this.timePeriod as keyof typeof this.selectedDates] as {day2: string}).day2
  }

  compareDate(date1: string, date2: string) {
    let [day, month, year] = date1.split("/");
    let monthIndex = parseInt(month) - 1;
    const d1 = new Date(parseInt(year), monthIndex, parseInt(day));

    [day, month, year] = date2.split("/");
    monthIndex = parseInt(month) - 1;
    const d2 = new Date(parseInt(year), monthIndex, parseInt(day));

    return d1 >= d2
  }

  formatDate(dateString: string) {
    const date = new Date(dateString);

    // Format the date using the toLocaleDateString() method
    const formattedDate = date.toLocaleDateString('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
    return formattedDate;
  }

  transformToDate(date: string){
    const splitDate = date.split("/");
    const day = splitDate[0];
    const month = splitDate[1];
    const year = splitDate[2];
    const formattedDate = year + "-" + month + "-" + day + "T00:00:00";
    return new Date(formattedDate)
  }

  getTodayDate(){
    const today = new Date();

    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0'); // Add leading zero for single-digit months
    const day = String(today.getDate()).padStart(2, '0'); // Add leading zero for single-digit days

    const formattedDate = `${year}-${month}-${day}T00:00:00`;

    return formattedDate
  }

  onTimePeriodChange(timePeriod: string) {
    this.timePeriod = timePeriod;
    if(this.timePeriod === 'day'){
      this.periodDate1 = this.selectedDates[this.timePeriod as keyof typeof this.selectedDates] as string
      this.periodDate2 = this.selectedDates[this.timePeriod as keyof typeof this.selectedDates] as string
    }else if(this.timePeriod === 'year'){
      this.periodDate1 = "01/01/" + this.selectedDates['year']
      this.periodDate2 = "31/12/" + this.selectedDates['year']
    }else if(this.timePeriod === 'month'){
      this.periodDate1 = '01/' + this.selectedDates['month'].month + '/' + this.selectedDates['month'].year
      this.periodDate2 = '01/' + (parseInt(this.selectedDates['month'].month)+1).toString() + '/' + this.selectedDates['month'].year
    }else if(this.timePeriod === 'quarter'){
      const q = this.selectedDates['quarter'].q
      if(q === 1){
        this.periodDate1 = "01/01/"+this.selectedDates['quarter'].year
        this.periodDate2 = "01/04/"+this.selectedDates['quarter'].year
      }else if(q == 2){
        this.periodDate1 = "01/04/"+this.selectedDates['quarter'].year
        this.periodDate2 = "01/07/"+this.selectedDates['quarter'].year
      }else if(q == 3){
        this.periodDate1 = "01/07/"+this.selectedDates['quarter'].year
        this.periodDate2 = "01/10/"+this.selectedDates['quarter'].year
      }else if(q == 4){
        this.periodDate1 = "01/10/"+this.selectedDates['quarter'].year
        this.periodDate2 = "31/12/"+this.selectedDates['quarter'].year
      }
    }else{
      this.periodDate1 = (this.selectedDates[this.timePeriod as keyof typeof this.selectedDates] as {day1: string}).day1
      this.periodDate2 = (this.selectedDates[this.timePeriod as keyof typeof this.selectedDates] as {day2: string}).day2
    }
    console.log('Data from child:', this.timePeriod);
  }

  getQuarter(ddate: string){
    const dateSplit: string[] = ddate.split("/")
    const month = dateSplit[1]
    if(month == '01' || month == '02' || month == '03'){
      return 1
    }
    if(month == '04' || month == '05' || month == '06'){
      return 2
    }
    if(month == '07' || month == '08' || month == '09'){
      return 3
    }
    else{
      return 4
    }
  }

  getIso8601Day() {
    return this.transformToIso8601(this.selectedDates["day"])
  }

  getIso8601Week() {
    return [this.transformToIso8601(this.selectedDates["week"].day1), this.transformToIso8601(this.selectedDates["week"].day2)]
  }

  getIso8601Week1Max() {
    const date = (this.getCustomMinusDaysDate(new Date(this.maxDate), 6))
    return this.transformToIso8601(date)
  }

  getIso8601Month() {
    const date = this.formatDate(this.today).split("/")[0] + "/" + this.selectedDates["month"].month + "/" + this.selectedDates["month"].year;
    return this.transformToIso8601(date)
  }

  getQuarterNum() {
    return "q" + this.selectedDates["quarter"].q
  }

  getIso8601QuarterYear() {
    const year = this.selectedDates["quarter"].year
    const date = this.formatDate(this.today).split("/")[0] + "/" + this.formatDate(this.today).split("/")[1] + "/" + this.selectedDates["quarter"].year;
    return this.transformToIso8601(date)
  }

  getIso8601Year() {
    const year = this.selectedDates["quarter"].year
    const date = this.formatDate(this.today).split("/")[0] + "/" + this.formatDate(this.today).split("/")[1] + "/" + this.selectedDates["year"];
    return this.transformToIso8601(date)
  }

  getIso8601AllDate() {
    return [this.transformToIso8601(this.selectedDates["all"].day1), this.transformToIso8601(this.selectedDates["all"].day2)]
  }

  getIso8601CustomDate() {
    return [this.transformToIso8601(this.selectedDates["custom"].day1), this.transformToIso8601(this.selectedDates["custom"].day2)]
  }

  transformToIso8601(dateString: string) {

    try {
      // Split the date string into day, month, and year components
      const [day, month, year] = dateString.split("/");

      // Check if all components are integers
      if (!day.match(/^\d+$/) || !month.match(/^\d+$/) || !year.match(/^\d+$/)) {
        return null;
      }

      // Convert components to integers
      const parsedDay = parseInt(day, 10);
      const parsedMonth = parseInt(month, 10) - 1; // Months are zero-indexed in JavaScript
      const parsedYear = parseInt(year, 10);

      // Validate date components
      if (parsedDay < 1 || parsedDay > 31 || parsedMonth < 0 || parsedMonth > 11 || parsedYear < 1) {
        return null;
      }

      // Format the date in ISO 8601 format using template literals
      return `${parsedYear.toString().padStart(4, "0")}-${(parsedMonth + 1).toString().padStart(2, "0")}-${parsedDay.toString().padStart(2, "0")}`;
    } catch (error) {
      console.error("Error parsing date string:", error);
      return null;
    }
  }

  async fetchAllData() {
    try {
      const result = await this.factorySimDataService.fetchDataById("sim", "1"); // Wait for the data to be fetched
      this.dailyData = this.factorySimDataService.getDailyProduction();
      this.minDate = this.getMinDate();
      this.maxDate = this.getMaxDate();
      this.selectedDates = {
        'day': this.formatDate(this.minDate),
        'week': {day1: this.formatDate(this.minDate), day2: this.getCustomDaysDate(new Date(this.minDate), 6)},
        'month': {"month": this.formatDate(this.minDate).split("/")[1], "year":this.formatDate(this.minDate).split("/")[2]},
        'quarter': {"q": this.getQuarter(this.formatDate(this.minDate)), "year":this.formatDate(this.minDate).split("/")[2]},
        'year': this.formatDate(this.minDate).split("/")[2],
        'all': {day1: this.formatDate(this.minDate), day2: this.formatDate(this.maxDate)},
        'custom': {day1: this.formatDate(this.minDate), day2: this.getCustomDaysDate(new Date(this.minDate), 1)}
      }
    } catch (error) {
        console.error('Error fetching data:', error);
    }
  }

  getMinDate(){
    let allDates = []
    for(const day in this.dailyData){
      const date = day.split("/")[2] + "/" + day.split("/")[1] + "/" +  day.split("/")[0]
      allDates.push(new Date(date));
    }
    let mnDate = allDates.reduce(function (a, b) {
        return a < b ? a : b;
    });
    return this.formatMinMaxDate(mnDate.toDateString());
  }

  getMaxDate(){
    let allDates = []
    for(const day in this.dailyData){
      const date = day.split("/")[2] + "/" + day.split("/")[1] + "/" +  day.split("/")[0]
      allDates.push(new Date(date));
    }

    let mxDate = allDates.reduce(function (a, b) {
      return a > b ? a : b;
    });
    return this.formatMinMaxDate(mxDate.toDateString());
  }

  formatMinMaxDate(dateString: string) {
    const months = {
      Jan: "01",
      Feb: "02",
      Mar: "03",
      Apr: "04",
      May: "05",
      Jun: "06",
      Jul: "07",
      Aug: "08",
      Sep: "09",
      Oct: "10",
      Nov: "11",
      Dec: "12"
    };

    const parts = dateString.split(" ");
    const day = parts[2];
    const someMonth = parts[1]; // Guaranteed to be a valid key
    const month = months[someMonth as keyof typeof months];
    const year = parts[3];

    return `${year}-${month}-${day.padStart(2, "0")}T00:00:00`;
  }

}
