import { TestBed } from '@angular/core/testing';

import { FactorySimDataService } from './factory-sim-data.service';

describe('FactorySimDataService', () => {
  let service: FactorySimDataService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(FactorySimDataService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
